-- Writes PNG: one part through Pixelmator Pro. Opens the staged SVG, exports it as a PNG with
-- transparency, close it without saving.
--   osascript export_part.applescript <staged svg> <png out> <width> <height> <open timeout s>
-- Prints "ok <width> <height>". Fails without exporting when the document doesn't open in time or
-- opens at another size. Never touches any other open document.
on run argv
	set src to item 1 of argv
	set dst to item 2 of argv
	set wantW to (item 3 of argv) as integer
	set wantH to (item 4 of argv) as integer
	set waitFor to (item 5 of argv) as integer
	set AppleScript's text item delimiters to "/"
	set fileName to last text item of src
	-- Pixelmator names an opened document after its file without the extension
	set AppleScript's text item delimiters to "."
	if (count of text items of fileName) > 1 then
		set base to (text items 1 thru -2 of fileName) as text
	else
		set base to fileName
	end if
	set AppleScript's text item delimiters to ""
	tell application "Pixelmator Pro"
		set openNames to name of every document
		if openNames contains base or openNames contains fileName then error "a document named " & base & " is already open"
		with timeout of waitFor seconds
			set d to open (POSIX file src)
		end timeout
		-- a large file can come back as missing value while it still loads
		repeat waitFor times
			if d is not missing value then exit repeat
			delay 1
			set found to (every document whose name is base)
			if (count of found) > 0 then set d to item 1 of found
		end repeat
		if d is missing value then error "timed out opening " & base
		set w to (width of d) as integer
		set h to (height of d) as integer
		if w is not wantW or h is not wantH then
			close d saving no
			error base & " opened at " & w & " x " & h & ", expected " & wantW & " x " & wantH
		end if
		with timeout of waitFor seconds
			export d to (POSIX file dst) as PNG
		end timeout
		close d saving no
	end tell
	return "ok " & w & " " & h
end run
