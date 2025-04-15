-- :::
-- :::: sample.lua ::::
-- ::::::::::::::::::::::
-- 
-- Author:      @espadonne (mfw)
-- Description: just my wezterm config.
--              but it's decorated for use with
--              my lil PyQt6 widget, wezztershier.
--              That tool looks at a WezTerm config with decorations
--              of my pleasing, and allows live editing of the terminal
--              emulator's visual effects via PyQT6 gui.
-- 


-- :::
-- :::: BOILERPLATE ::::
-- :::::::::::::::::::::::
-- 
local wezterm = require 'wezterm'

local config = {}
if wezterm.config_builder then
  config = wezterm.config_builder()
end


-- :::
-- :::: TUNER FOR WEZZTERSHIER ::::
-- ::::: :::::::::::::::::::::: :::::

-- <<TUNER-START>>
-- @ui: slider(min=10, max=42, step=1) type=int
config.font_size = 18
-- @ui: slider(min=0.05, max=1.0, step=0.01) type=float
config.window_background_opacity = 0.46
-- @ui: select(options="Gruvbox Dark, Gruvbox Light, Catppuccin Mocha") type=string
config.color_scheme = "Catppuccin Mocha"
-- @ui: slider(min=1, max=100, step=1) type=int
config.macos_window_background_blur = 17
-- <<TUNER-END>>


-- :::
-- :::: TO ADD HANDLING FOR :: later ::::
-- ::::: :::::::::::::::::::::::::::: :::::
-- 
config.debug_key_events = false
config.enable_scroll_bar = true
config.colors = config.colors or {}
config.colors.background = "#333333"
config.window_decorations = "RESIZE"
config.pane_focus_follows_mouse = true
config.native_macos_fullscreen_mode = true
config.hide_tab_bar_if_only_one_tab = true
config.font = wezterm.font("JetBrains Mono")


-- :::
-- :::: DYNAMICS :: the spice of life ::::
-- ::::: ::::::::::::::::::::::::::::: :::::
-- 
-- NOTE:  just a clock for now lol, and I hide
--        it most of the time, too ..lol
wezterm.on("update-right-status", function(window, pane)
  local date = wezterm.strftime("  %Y-%m-%d %H:%M:%S    ")
  window:set_right_status(date)
end)


-- :::
-- :::: KEYBINDS :: my onetrue ::::
-- ::::: :::::::::::::::::::::: :::::
-- 
config.keys = {
  {
    key = "R",
    mods = "CTRL|SHIFT",
    action = wezterm.action.ReloadConfiguration,
  },
  {
    key = "W",
    mods = "CTRL|SHIFT",
    action = wezterm.action.CloseCurrentTab { confirm = true },
  },
  {
    key = "T",
    mods = "CTRL|SHIFT",
    action = wezterm.action.SpawnTab("CurrentPaneDomain"),
  },
  {
    key = "UpArrow",
    mods = "CMD|OPT|CTRL",
    action = wezterm.action.SplitVertical { domain = "CurrentPaneDomain" },
  },
  {
    key = "RightArrow",
    mods = "CMD|OPT|CTRL",
    action = wezterm.action.SplitHorizontal { domain = "CurrentPaneDomain" },
  },
}


-- :::
-- :::: TAB BAR SETTINGS ::::
-- ::::: :::::::::::::::: :::::
--
-- NOTE:  really just colors rn;
--        the live timestamp is scripted.
config.colors.tab_bar = {
  background = "#333333",
  active_tab = {
    bg_color = "#333333",
    fg_color = "#FFFFFF",
  },
  inactive_tab = {
    bg_color = "#333333",
    fg_color = "#777777",
  },
  inactive_tab_hover = {
    bg_color = "#444444",
    fg_color = "#DDDDDD",
  },
  new_tab = {
    bg_color = "#333333",
    fg_color = "#FFFFFF",
  },
  new_tab_hover = {
    bg_color = "#444444",
    fg_color = "#FFFFFF",
  },
}

return config
