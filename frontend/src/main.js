import { draw } from "./render.js"
import { load, subscribe, watch } from "./store.js"

const root = document.querySelector("#app")
subscribe((state) => draw(root, state))
load()
watch()
