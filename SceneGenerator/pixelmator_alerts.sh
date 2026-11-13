#!/bin/sh
# Writes nothing: lists or dismisses Pixelmator Pro's "couldn't be opened" / InternalError alerts.
#   ./pixelmator_alerts.sh            list them
#   ./pixelmator_alerts.sh dismiss    click OK until none are left
# Prints "none" when there are none. A failed open stacks more than one alert, each shown only
# once the one in front of it is closed, so dismiss repeats until a pass finds nothing. System Events needs Accessibility permission, which
# Keyboard Maestro Engine has, so the script runs as a one-off Engine action. The first run
# asks macOS to let this terminal control Keyboard Maestro Engine (Privacy > Automation).
set -e
cd "$(dirname "$0")"
mode=${1:-list}
action=/tmp/pixelmator_alerts_action.plist
python3 "$HOME/.claude/skills/keyboard-maestro-scripting/scripts/km_action_xml.py" applescript \
	--file pixelmator_alerts.applescript --variable PixelmatorAlerts > "$action"

pass() {
	echo "$1" > /tmp/pixelmator_alerts_mode
	osascript -e "set p to (read POSIX file \"$action\" as «class utf8»)" \
		-e 'with timeout of 60 seconds' \
		-e 'tell application "Keyboard Maestro Engine" to do script p' \
		-e 'end timeout' > /dev/null
	osascript -e 'tell application "Keyboard Maestro Engine" to getvariable "PixelmatorAlerts"'
	rm -f /tmp/pixelmator_alerts_mode
}

if [ "$mode" != dismiss ]; then
	pass list
	exit
fi
dismissed=0
for attempt in 1 2 3 4 5 6 7 8 9 10; do
	result=$(pass dismiss)
	if [ "$result" = none ]; then
		[ "$dismissed" = 0 ] && echo none
		exit 0
	fi
	printf '%s\n' "$result"
	dismissed=1
	sleep 1
done
echo "alerts still showing after 10 passes" >&2
exit 1
