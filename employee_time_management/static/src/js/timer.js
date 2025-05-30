/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { parseFloatTime } from "@web/views/fields/parsers";
import { useInputField } from "@web/views/fields/input_field_hook";

const { Component, useState, onWillUpdateProps, onWillStart, onWillDestroy } = owl;

function formatMinutes(value) {
    if (value === false) {
        return "";
    }
    const isNegative = value < 0;
    if (isNegative) {
        value = Math.abs(value);
    }
    let hours = Math.floor(value / 60);
    let minutes = Math.floor(value % 60);
    let seconds = Math.floor((value % 1) * 60);
    seconds = `${seconds}`.padStart(2, "0");
    minutes = `${minutes}`.padStart(2, "0");
    return `${isNegative ? "-" : ""}${hours}:${minutes}:${seconds}`;
}

export class BreakTimer extends Component {
    setup() {
        this.orm = useService('orm');
        this.state = useState({
            // duration is expected to be given in minutes
            duration:
                this.props.value !== undefined ? this.props.value : this.props.record.data.duration,
        });
        useInputField({
            getValue: () => this.durationFormatted,
            refName: "numpadDecimal",
            parse: (v) => parseFloatTime(v),
        });

        this.ongoing =
            this.props.ongoing !== undefined
                ? this.props.ongoing
                : this.props.record.data.is_user_working;

        onWillStart(async () => {
            if(this.props.ongoing === undefined && !this.props.record.model.useSampleModel && this.props.record.data.break_timer) {
                const additionalDuration = await this.orm.call('attendance.breaktime', 'get_working_duration', [this.props.record.resId]);
                this.state.duration += additionalDuration;
            }
            if (this.ongoing) {
                this._runTimer();
            }
        });
        onWillUpdateProps((nextProps) => {
            const newOngoing =
                "ongoing" in nextProps
                    ? nextProps.ongoing
                    : "record" in nextProps && nextProps.record.data.is_user_working;
            const rerun = !this.ongoing && newOngoing;
            this.ongoing = newOngoing;
            if (rerun) {
                this.state.duration = nextProps.value;
                this._runTimer();
            }
        });
        onWillDestroy(() => clearTimeout(this.timer));
    }

    get durationFormatted() {
        return formatMinutes(this.state.duration);
    }

    _runTimer() {
        this.timer = setTimeout(() => {
            if (this.ongoing) {
                this.state.duration += 1 / 60;
                this._runTimer();
            }
        }, 1000);
    }

    // add hour to timer
    addHour() {
        this.state.duration += 60;
    }
}

BreakTimer.supportedTypes = ["float"];
BreakTimer.template = "BreakTimerTemplate";

registry.category("fields").add("break_timer", BreakTimer);
registry.category("formatters").add("break_timer", formatMinutes);