#!/usr/bin/env fish


for file in *;
  exiftool -TagsFromFile ~/Applications/panel-attack/james-panel-game/client/assets/default_data/characters/Magellan/telegraph/$file -creator -rights -attributionname -copyright -license -title -artist -contact -comment "~/Applications/panel-attack/james-panel-game/client/assets/default_data/characters/Madam Q/telegraph/$file"
end
