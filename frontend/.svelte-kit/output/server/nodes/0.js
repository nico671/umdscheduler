

export const index = 0;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/fallbacks/layout.svelte.js')).default;
export const imports = ["_app/immutable/nodes/0.B7GHCk5l.js","_app/immutable/chunks/SAxT4GhW.js","_app/immutable/chunks/BpTswYDJ.js"];
export const stylesheets = [];
export const fonts = [];
