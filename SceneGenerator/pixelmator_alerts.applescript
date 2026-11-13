-- Writes nothing: lists Pixelmator Pro's open-failure alerts, or clicks OK on them when the first line is "dismiss".
-- Run through Keyboard Maestro Engine (see pixelmator_alerts.sh), which has the Accessibility
-- permission System Events needs. Only alerts whose text matches ALERT_TEXTS are touched.
-- Pixelmator writes these with typographic apostrophes, so match the words around them.
property ALERT_TEXTS : {"be opened.", "is damaged", "compatible with Pixelmator", "InternalError"}

on matchesAlert(texts)
	repeat with t in texts
		repeat with a in ALERT_TEXTS
			if (t as text) contains (a as text) then return true
		end repeat
	end repeat
	return false
end matchesAlert

on handleContainer(c, dismiss)
	tell application "System Events"
		set texts to value of static texts of c
		if not my matchesAlert(texts) then return ""
		set summary to "alert: " & (item 1 of texts)
		if dismiss then
			click (first button of c whose name is "OK")
			set summary to summary & " -> OK"
		end if
		return summary & linefeed
	end tell
end handleContainer

set dismiss to (do shell script "cat /tmp/pixelmator_alerts_mode 2>/dev/null || echo list") is "dismiss"
set out to ""
tell application "System Events"
	if not (exists process "Pixelmator Pro") then return "not running"
	tell process "Pixelmator Pro"
		repeat with w in windows
			try
				set out to out & my handleContainer(w, dismiss)
			end try
			try
				repeat with s in sheets of w
					set out to out & my handleContainer(s, dismiss)
				end repeat
			end try
		end repeat
	end tell
end tell
if out is "" then return "none"
return out
