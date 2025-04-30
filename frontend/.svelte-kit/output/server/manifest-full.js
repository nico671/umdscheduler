export const manifest = (() => {
function __memo(fn) {
	let value;
	return () => value ??= (value = fn());
}

return {
	appDir: "_app",
	appPath: "_app",
	assets: new Set(["favicon.png","fonts/Afacad_Flux/AfacadFlux-VariableFont_slnt,wght.ttf","fonts/Afacad_Flux/OFL.txt","fonts/Afacad_Flux/README.txt","fonts/Afacad_Flux/static/AfacadFlux-Black.ttf","fonts/Afacad_Flux/static/AfacadFlux-Bold.ttf","fonts/Afacad_Flux/static/AfacadFlux-ExtraBold.ttf","fonts/Afacad_Flux/static/AfacadFlux-ExtraLight.ttf","fonts/Afacad_Flux/static/AfacadFlux-Light.ttf","fonts/Afacad_Flux/static/AfacadFlux-Medium.ttf","fonts/Afacad_Flux/static/AfacadFlux-Regular.ttf","fonts/Afacad_Flux/static/AfacadFlux-SemiBold.ttf","fonts/Afacad_Flux/static/AfacadFlux-Thin.ttf"]),
	mimeTypes: {".png":"image/png",".ttf":"font/ttf",".txt":"text/plain"},
	_: {
		client: {start:"_app/immutable/entry/start.1K8OA06_.js",app:"_app/immutable/entry/app.CRiZPpoQ.js",imports:["_app/immutable/entry/start.1K8OA06_.js","_app/immutable/chunks/CzX_qRbF.js","_app/immutable/chunks/BpTswYDJ.js","_app/immutable/chunks/UFYTEpbQ.js","_app/immutable/entry/app.CRiZPpoQ.js","_app/immutable/chunks/BpTswYDJ.js","_app/immutable/chunks/Du5amvOE.js","_app/immutable/chunks/SAxT4GhW.js","_app/immutable/chunks/BIKkHqwm.js","_app/immutable/chunks/UFYTEpbQ.js"],stylesheets:[],fonts:[],uses_env_dynamic_public:false},
		nodes: [
			__memo(() => import('./nodes/0.js')),
			__memo(() => import('./nodes/1.js')),
			__memo(() => import('./nodes/2.js'))
		],
		routes: [
			{
				id: "/",
				pattern: /^\/$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 2 },
				endpoint: null
			}
		],
		prerendered_routes: new Set([]),
		matchers: async () => {
			
			return {  };
		},
		server_assets: {}
	}
}
})();
