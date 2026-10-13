"use strict";

// Geometría ilustrativa de un motor de inducción. No reproduce una marca,
// dimensiones de fabricación ni la geometría desconocida del rodamiento real.
// Toda rotación se proyecta sobre un eje horizontal; la velocidad de dibujo
// es deliberadamente legible y no equivale a las rpm ni al muestreo de señales.
window.MotorMechanics = (() => {
    const byId = id => document.getElementById(id);
    const tau = 2 * Math.PI;
    const clamp = v => Math.max(0, Math.min(1, v));
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
    const parts = {
        de: {title: "Rodamiento delantero · DE", zone: "de", info: "Soporta el eje junto al acoplamiento. Se representan pistas, jaula y bolas. La vista ampliada permite observar el contacto y los efectos impuestos.", label: "RODAMIENTO DE"},
        nde: {title: "Rodamiento posterior · NDE", zone: "nde", info: "Apoyo del eje en el lado del ventilador. Recibe parte de la fricción y del desequilibrio del modelo; la desalineación pesa más en DE.", label: "RODAMIENTO NDE"},
        stator: {title: "Estator y bobinados", zone: "casing", info: "Núcleo y bobinas fijos alrededor del rotor. El halo térmico utiliza la temperatura superficial de carcasa; no existe un canal de temperatura interna de bobina.", label: "ESTATOR FIJO"},
        rotor: {title: "Rotor de jaula", zone: "casing", info: "Gira dentro del estator y transmite el movimiento al eje. El marcador excéntrico aparece al imponer desequilibrio; su tamaño es una amplificación visual.", label: "ROTOR / GIRO"},
        shaft: {title: "Eje y transmisión", zone: "de", info: "Une rotor, apoyos y acoplamiento. La desalineación se representa con ejes desplazados y una flecha en DE; no calcula esfuerzos ni deformación real del acero.", label: "EJE / TRANSMISIÓN"},
        fan: {title: "Ventilador posterior", zone: "nde", info: "Gira con el eje. Las líneas de aire siguen el ajuste de ventilación: menos refrigeración reduce el flujo dibujado y eleva el calor de forma gradual.", label: "VENTILACIÓN"},
        casing: {title: "Carcasa y fijación", zone: "casing", info: "Aletas y apoyos exteriores. La transparencia permite observar el motor sin retirarlos. La holgura impuesta resalta los pernos de montaje.", label: "CARCASA / MONTAJE"}
    };
    let state = null, component = "de", selectZone = null, shell = true;
    let angle = 0, previous = 0, active = false, animationId = null;
    const rotating = {bars: [], balls: [], fan: [], detailBalls: []};

    function bearing(key, cx) {
        return `<g id="visual-${key}" class="machine-zone internal-bearing" data-part="${key}">
          <ellipse cx="${cx}" cy="217" rx="23" ry="43" fill="url(#bearing-steel)" stroke="#d2e3e5" stroke-width="1.2"/>
          <ellipse cx="${cx}" cy="217" rx="17" ry="34" fill="#0a1e2a" stroke="#526b7c" stroke-width="2"/>
          <ellipse cx="${cx}" cy="217" rx="14" ry="29" fill="none" stroke="#b99560" stroke-width="2"/>
          <g id="balls-${key}"></g>
          <ellipse cx="${cx}" cy="217" rx="9" ry="19" fill="url(#machined)" stroke="#cbdadf"/>
          <ellipse cx="${cx}" cy="217" rx="5" ry="10" fill="url(#machined)" stroke="#6f94a6"/>
          <ellipse class="bearing-friction cause-effect" cx="${cx}" cy="217" rx="17" ry="34" fill="none" stroke="#ff9e50" stroke-width="3"/>
          <g class="bearing-dirt cause-effect" fill="#dcac77"><circle cx="${cx-7}" cy="190" r="2"/><circle cx="${cx+9}" cy="234" r="1.8"/><circle cx="${cx-12}" cy="220" r="1.7"/></g>
          <path class="bearing-defect cause-effect" d="M${cx+8} 180l7 6-4 4 5 5-3 6" fill="none" stroke="#ff6c64" stroke-width="3"/>
          <ellipse class="heat" cx="${cx}" cy="217" rx="51" ry="66" fill="url(#hot)"/>
          <ellipse class="selection-ring" cx="${cx}" cy="217" rx="27" ry="47"/>
        </g>`;
    }

    function scene() {
        return `<defs>
          <pattern id="grid" width="35" height="35" patternUnits="userSpaceOnUse"><path d="M35 0H0V35" fill="none" stroke="#173442" stroke-width=".65"/></pattern>
          <linearGradient id="paint" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#548aaf"/><stop offset=".16" stop-color="#254f75"/><stop offset=".46" stop-color="#163a59"/><stop offset=".8" stop-color="#092438"/><stop offset="1" stop-color="#2d536e"/></linearGradient>
          <linearGradient id="machined" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#718896"/><stop offset=".18" stop-color="#e0eced"/><stop offset=".42" stop-color="#809dac"/><stop offset=".66" stop-color="#364f61"/><stop offset=".87" stop-color="#9bb6be"/><stop offset="1" stop-color="#34485a"/></linearGradient>
          <linearGradient id="bearing-steel"><stop stop-color="#314b60"/><stop offset=".32" stop-color="#bdd0d6"/><stop offset=".52" stop-color="#7893a3"/><stop offset=".8" stop-color="#d4e1e3"/><stop offset="1" stop-color="#486777"/></linearGradient>
          <linearGradient id="copper" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#ffe1a2"/><stop offset=".27" stop-color="#c9874f"/><stop offset=".56" stop-color="#82502d"/><stop offset=".83" stop-color="#e9ae70"/><stop offset="1" stop-color="#75432b"/></linearGradient>
          <radialGradient id="ball"><stop offset="0" stop-color="#f3fbf8"/><stop offset=".35" stop-color="#bdced5"/><stop offset="1" stop-color="#456273"/></radialGradient>
          <radialGradient id="hot"><stop stop-color="#ff493c" stop-opacity=".9"/><stop offset=".5" stop-color="#ff633c" stop-opacity=".48"/><stop offset="1" stop-color="#fe493b" stop-opacity="0"/></radialGradient>
          <radialGradient id="halo"><stop stop-color="#32bdcb" stop-opacity=".14"/><stop offset="1" stop-color="#20b6ca" stop-opacity="0"/></radialGradient>
          <pattern id="laminations" width="5" height="10" patternUnits="userSpaceOnUse"><path d="M1 0V10" stroke="#8ca1ad" stroke-opacity=".35"/><path d="M3 0V10" stroke="#071925" stroke-opacity=".8"/></pattern>
          <linearGradient id="glass" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#6795b9" stop-opacity=".4"/><stop offset=".5" stop-color="#1c4260" stop-opacity=".12"/><stop offset="1" stop-color="#377b9f" stop-opacity=".45"/></linearGradient>
        </defs>
        <rect width="1000" height="460" fill="url(#grid)" opacity=".55"/>
        <ellipse cx="514" cy="245" rx="394" ry="195" fill="url(#halo)"/>
        <ellipse cx="517" cy="346" rx="333" ry="15" fill="#010d17" opacity=".65"/>
        <g id="water-circuit">
          <path class="pipe-shadow" d="M100 336H795V270 M730 160V65H100V246"/>
          <path class="pipe" d="M100 336H795V270 M730 160V65H100V246"/>
          <path class="flow" d="M100 336H795V270 M730 160V65H100V246"/>
          <path d="M48 245H145V334Q100 358 48 334Z" fill="#082b38" stroke="#49808f" stroke-width="1.5"/>
          <path d="M49 277Q71 267 98 277T144 277V332Q96 351 49 332Z" fill="#188398" opacity=".4"/>
          <ellipse cx="96" cy="245" rx="49" ry="11" fill="#102e3d" stroke="#537e8c"/>
          <path d="M60 292H132M60 315H132" stroke="#42a6b0" opacity=".35"/>
          <text x="95" y="305" text-anchor="middle" class="part-label">H₂O</text><text x="95" y="379" text-anchor="middle">AGUA LIMPIA</text>
          <g id="valve-visual"><path d="m330 54 23 11-23 11Z m46 0-23 11 23 11Z" fill="#17404d" stroke="#75bfba"/><path d="M353 39V59M337 39h32" stroke="#7bc9bc" stroke-width="3"/><text x="435" y="48" text-anchor="middle" class="small-label" id="valve-caption">VÁLVULA 100 %</text></g>
          <path d="m497 60 -9 5 9 5 M498 331l9 5-9 5" fill="none" stroke="#75d7cc"/>
        </g>
        <g id="foundation"><path d="M181 310 247 334H842L780 310Z" fill="#274353" stroke="#557081"/><path d="M247 334V349H842V334" fill="#112536" stroke="#3c596e"/><path d="M259 336h569" stroke="#7c99a8" opacity=".35"/><path d="M275 336v10M378 336v10M750 336v10M818 336v10" stroke="#466477"/></g>
        <g id="motor-assembly">
          <g id="motor-feet" class="mechanical-part" data-part="casing"><path d="M298 279v29l-12 7h63v-33 M451 279v29l-12 7h60v-33" fill="url(#paint)" stroke="#7096ad"/>
            <g id="mount-bolts"><ellipse cx="304" cy="309" rx="7" ry="3" fill="url(#machined)" stroke="#a9c0c8"/><ellipse cx="470" cy="309" rx="7" ry="3" fill="url(#machined)" stroke="#a9c0c8"/></g>
          </g>
          <g id="visual-casing" class="machine-zone">
            <g id="part-stator" class="mechanical-part" data-part="stator">
              <path d="M300 162H469L486 178V256L469 273H300Z" fill="url(#machined)" stroke="#90aab6"/>
              <path d="M302 165H468V270H302Z" fill="url(#laminations)"/>
              <rect x="315" y="189" width="146" height="57" fill="#071522" stroke="#495f70"/>
              <ellipse cx="301" cy="217" rx="17" ry="54" fill="url(#copper)" stroke="#efbc7e"/>
              <ellipse cx="301" cy="217" rx="9" ry="33" fill="#122734" stroke="#694b36"/>
              <path d="M312 171H455M312 180H458M311 254H458M310 262H455" stroke="url(#copper)" stroke-width="5"/>
              <ellipse cx="469" cy="217" rx="17" ry="54" fill="url(#copper)" stroke="#efbc7e"/>
              <ellipse cx="469" cy="217" rx="10" ry="34" fill="#112839" stroke="#8c603e"/>
              <g id="winding-lines" fill="none" stroke="#ffcd8c" stroke-width=".9" opacity=".65"></g>
              <rect class="selection-ring" x="284" y="158" width="203" height="118" rx="18"/>
            </g>
            <g id="part-shaft" class="mechanical-part" data-part="shaft"><path d="M235 210H554V224H235Z" fill="url(#machined)" stroke="#a8c1cb" stroke-width=".8"/><path d="M243 213H551" stroke="#ecf6f1" opacity=".6"/><path d="M519 210h20v-3h-20Z" fill="#92a5ac"/>
              <path class="selection-ring" d="M233 207H552V227H233Z"/>
            </g>
            <g id="part-rotor" class="mechanical-part" data-part="rotor">
              <g id="rotor-body"><rect x="326" y="190" width="128" height="54" fill="url(#machined)" stroke="#afc2c9"/>
                <rect x="329" y="191" width="118" height="52" fill="url(#laminations)" opacity=".85"/>
                <ellipse cx="326" cy="217" rx="8" ry="27" fill="url(#bearing-steel)" stroke="#adbec3"/><ellipse cx="454" cy="217" rx="8" ry="27" fill="url(#bearing-steel)" stroke="#bdd0d4"/>
                <g id="rotor-bars"></g><ellipse cx="454" cy="217" rx="3" ry="8" fill="#7594a2"/>
                <circle id="eccentric-mass" class="cause-effect" cx="405" cy="195" r="5" fill="#ffb468" stroke="#ffe0aa"/>
              </g><rect class="selection-ring" x="316" y="185" width="147" height="64" rx="14"/>
            </g>
            <g id="motor-shell" class="motor-shell">
              <path d="M268 158 290 141H488L520 158V267L492 286H291L268 270Z" fill="url(#paint)" stroke="#8fb7cc" stroke-width="1.3"/>
              <path d="M293 143H486L514 158H274Z" fill="#94b4c7" opacity=".23"/>
              <g id="motor-fins"></g>
              <ellipse cx="269" cy="217" rx="27" ry="64" fill="url(#paint)" stroke="#96b5c3"/>
              <ellipse cx="511" cy="217" rx="25" ry="65" fill="url(#paint)" stroke="#a3bfcc"/>
              <path d="M511 158c-20 22-20 95 0 119" fill="none" stroke="#d2e0e5" opacity=".35"/>
            </g>
            <path id="glass-outline" d="M268 158 290 141H488L520 158V267L492 286H291L268 270Z" fill="url(#glass)" stroke="#8acddd" stroke-width="1.1"/>
            <g id="terminal-box"><path d="M337 113 354 101H414L433 113V143H337Z" fill="url(#paint)" stroke="#789eaf"/><path d="M338 114h94M354 102v12" stroke="#b1c8d4" opacity=".5"/><rect x="345" y="121" width="69" height="15" rx="2" fill="#122d40" stroke="#608da3"/><text x="380" y="132" text-anchor="middle" class="nameplate">5 HP / 1~</text><circle cx="431" cy="129" r="5" fill="url(#machined)" stroke="#dae7e7"/><path d="M432 129h13q8 0 8 8v8" stroke="#496170" stroke-width="5" fill="none"/></g>
            <ellipse class="heat" cx="386" cy="215" rx="131" ry="91" fill="url(#hot)"/>
          </g>
          <g id="part-fan" class="mechanical-part" data-part="fan"><ellipse cx="240" cy="217" rx="14" ry="48" fill="#172f42" stroke="#6b97ac"/><g id="fan-blades"></g><ellipse cx="240" cy="217" rx="4" ry="9" fill="url(#machined)"/>
            <g class="fan-cover"><path d="M221 171h19v92h-19q-18-47 0-92Z" fill="url(#paint)" stroke="#749aac"/><path d="M221 180v75M215 191v52M228 175v84M235 175v84" stroke="#6793a8" stroke-width="2"/></g><ellipse class="selection-ring" cx="239" cy="217" rx="20" ry="51"/>
          </g>
          <g id="air-streams" fill="none" stroke="#65c7d2" stroke-width="1.2" stroke-dasharray="7 8"><path d="M213 156Q268 127 317 157H488"/><path d="M214 274Q275 299 313 278H486"/></g>
          ${bearing("nde", 275)}${bearing("de", 507)}
          <path id="alignment-force" class="cause-effect" d="M527 169V198m-5-6 5 6 5-6" fill="none" stroke="#ffc180" stroke-width="2"/>
        </g>
        <g id="visual-coupling" class="machine-zone">
          <path d="M550 196h19v42h-19Z" fill="url(#machined)" stroke="#b5c9d0"/>
          <ellipse cx="552" cy="217" rx="7" ry="21" fill="url(#bearing-steel)" stroke="#d2e0e5"/>
          <path d="M570 192h26v50h-26Z" fill="#142936" stroke="#638889"/>
          <path d="M575 195v44M583 194v46M591 195v44" stroke="#559b91" stroke-width="3"/>
          <path d="M600 197h17v40h-17Z" fill="url(#machined)" stroke="#bed4dc"/>
          <ellipse cx="616" cy="217" rx="6" ry="20" fill="url(#bearing-steel)" stroke="#bbd0d8"/>
          <path d="M622 209h37v16h-37" fill="url(#machined)" stroke="#bdd0d7"/>
          <path id="shaft-axis" d="M534 217H651" stroke="#80cfc2" stroke-dasharray="4 5" opacity=".65"/>
          <circle cx="558" cy="204" r="2" fill="#0b2031"/><circle cx="608" cy="231" r="2" fill="#0b2031"/>
        </g>
        <g id="visual-pump" class="machine-zone">
          <path d="M657 214v46l22 30h96l20-33-11-53q-14-47-68-44Z" fill="url(#paint)" stroke="#92afc0" stroke-width="1.5"/>
          <path d="M679 291v18h34v-21M752 289v20h29v-25" fill="url(#paint)" stroke="#7090a7"/>
          <circle cx="719" cy="225" r="48" fill="url(#machined)" stroke="#acbfc7" stroke-width="1.3"/>
          <circle cx="719" cy="225" r="41" fill="url(#paint)" stroke="#48778d"/>
          <circle cx="719" cy="225" r="32" fill="#102b3e" stroke="#76b7bd"/>
          <g id="impeller"><path d="M719 225q-27-36-31-11 20 0 31 11M719 225q36-27 11-31 0 20-11 31M719 225q27 36 31 11-20 0-31-11M719 225q-36 27-11 31 0-20 11-31" fill="#417587" stroke="#84cbbf"/></g>
          <circle cx="719" cy="225" r="7" fill="url(#ball)"/>
          <g id="pump-bolts" fill="url(#ball)" stroke="#506b7b"></g>
          <path d="M708 176v-23h41v23M781 244h23v30h-23" fill="url(#paint)" stroke="#8daebb"/>
          <rect x="700" y="150" width="56" height="9" rx="2" fill="url(#machined)" stroke="#afc4cb"/>
          <rect x="802" y="237" width="9" height="45" rx="2" fill="url(#machined)" stroke="#afc4cb"/>
          <g id="pump-bubbles" class="cause-effect" fill="none" stroke="#a1d8d7"><circle cx="702" cy="224" r="4"/><circle cx="732" cy="207" r="3"/><circle cx="729" cy="239" r="5"/></g>
          <ellipse class="heat" cx="719" cy="226" rx="84" ry="79" fill="url(#hot)"/>
        </g>
        <g class="select-zones">
          <g class="zone-hotspot" data-zone="nde" role="button" tabindex="0" aria-label="Seleccionar rodamiento posterior NDE"><path d="M275 176V125H166"/><circle cx="275" cy="176" r="4"/><text x="153" y="110">01 / NDE</text><text x="153" y="126" class="zone-reading" id="svg-nde">—</text></g>
          <g class="zone-hotspot" data-zone="casing" role="button" tabindex="0" aria-label="Seleccionar carcasa del motor"><path d="M367 272V389H292"/><circle cx="367" cy="272" r="4"/><text x="276" y="405">02 / CARCASA</text><text x="276" y="421" class="zone-reading" id="svg-casing">—</text></g>
          <g class="zone-hotspot selected" data-zone="de" role="button" tabindex="0" aria-label="Seleccionar rodamiento delantero DE"><path d="M507 174V111H550"/><circle cx="507" cy="174" r="4"/><text x="551" y="104">03 / DE</text><text x="551" y="121" class="zone-reading" id="svg-de">—</text></g>
          <g class="zone-hotspot" data-zone="pump" role="button" tabindex="0" aria-label="Seleccionar bomba de agua"><path d="M757 225H871V172"/><circle cx="757" cy="225" r="4"/><text x="819" y="151">04 / BOMBA</text><text x="819" y="168" class="zone-reading" id="svg-pump">—</text></g>
        </g>
        <g class="overview-labels"><text x="376" y="371" text-anchor="middle" class="part-caption">MOTOR / CARCASA TRANSLÚCIDA</text><text x="584" y="274" text-anchor="middle" class="part-caption">ACOPLAMIENTO ELÁSTICO</text><text x="729" y="369" text-anchor="middle" class="part-caption">BOMBA CENTRÍFUGA</text></g>
        <g class="motor-labels"><path d="M354 165V148h-28M409 204v-45h22"/><text x="304" y="136">ESTATOR / FIJO</text><text x="432" y="157">ROTOR / GIRO</text><text x="293" y="296">EJE → TRANSMISIÓN</text></g>`;
    }

    function svgElement(name, attributes, parent) {
        const el = document.createElementNS("http://www.w3.org/2000/svg", name);
        for (const [key, value] of Object.entries(attributes)) el.setAttribute(key, value);
        if (parent) parent.append(el);
        return el;
    }

    function buildDetail() {
        byId("bearing-detail").innerHTML = `<defs><radialGradient id="detail-metal"><stop stop-color="#eef8f7"/><stop offset=".5" stop-color="#8099a6"/><stop offset="1" stop-color="#294355"/></radialGradient></defs>
          <circle cx="95" cy="88" r="67" fill="#122b3d" stroke="#819dab" stroke-width="3"/>
          <circle cx="95" cy="88" r="56" fill="#071622" stroke="#bdd1d8" stroke-width="6"/>
          <circle cx="95" cy="88" r="43" fill="none" stroke="#a68b64" stroke-width="2"/>
          <g id="detail-balls"></g><circle cx="95" cy="88" r="30" fill="url(#detail-metal)" stroke="#c6d6dc"/>
          <circle cx="95" cy="88" r="21" fill="#0f2636" stroke="#688fa1" stroke-width="2"/>
          <circle id="detail-friction" class="cause-effect" cx="95" cy="88" r="52" fill="none" stroke="#ffa757" stroke-width="5"/>
          <path id="detail-defect" class="cause-effect" d="M137 44l-3 6 8 1-3 6 7 2" fill="none" stroke="#ff6c68" stroke-width="4"/>
          <g id="detail-dirt" class="cause-effect" fill="#e8ac66"><circle cx="54" cy="66" r="2.5"/><circle cx="124" cy="119" r="3"/><circle cx="108" cy="38" r="2.5"/></g>
          <circle id="detail-heat" class="heat" cx="95" cy="88" r="74" fill="url(#hot)"/>
          <text x="95" y="178" text-anchor="middle" id="detail-label">RODAMIENTO DE</text>`;
        for (let i = 0; i < 8; i++) rotating.detailBalls.push(svgElement("circle", {r: 9, fill: "url(#detail-metal)", stroke: "#d7e9e6", "stroke-width": .6}, byId("detail-balls")));
    }

    function init(onSelectZone) {
        selectZone = onSelectZone;
        byId("plant-svg").innerHTML = scene();
        buildDetail();
        for (let y = 160; y < 278; y += 9) {
            svgElement("path", {d: `M293 ${y}H489l24-14`, fill: "none", stroke: "#0a2438", "stroke-width": 4}, byId("motor-fins"));
            svgElement("path", {d: `M293 ${y-2}H489l24-14`, fill: "none", stroke: "#93b2c5", "stroke-width": 1.5}, byId("motor-fins"));
        }
        for (let i = 0; i < 8; i++) {
            const a = i * tau / 8;
            svgElement("circle", {cx: 719 + 44 * Math.cos(a), cy: 225 + 44 * Math.sin(a), r: 2.5}, byId("pump-bolts"));
        }
        for (let i = 0; i < 7; i++) {
            const d = i * 2;
            svgElement("path", {d: `M${293+d} 169q-25 47 0 96 M${462+d} 169q25 47 0 96`}, byId("winding-lines"));
        }
        for (let i = 0; i < 10; i++) rotating.bars.push(svgElement("path", {fill: "none", stroke: "#d7c49f", "stroke-width": 2}, byId("rotor-bars")));
        for (const [key, cx] of [["nde", 275], ["de", 507]]) {
            for (let i = 0; i < 8; i++) rotating.balls.push({el: svgElement("ellipse", {rx: 3.6, ry: 5.3, fill: "url(#ball)", stroke: "#b8d1d9", "stroke-width": .6}, byId("balls-" + key)), i, cx});
        }
        for (let i = 0; i < 6; i++) rotating.fan.push(svgElement("path", {fill: "#88aebb", stroke: "#c7d7dc", "stroke-width": .5}, byId("fan-blades")));
        document.querySelectorAll("[data-part]").forEach(el => {
            el.setAttribute("role", "button");
            el.setAttribute("tabindex", "0");
            el.setAttribute("aria-label", "Explorar " + parts[el.dataset.part].title);
            el.addEventListener("click", () => choose(el.dataset.part));
            el.addEventListener("keydown", event => {
                if (event.key === "Enter" || event.key === " ") {event.preventDefault(); choose(el.dataset.part);}
            });
        });
        for (const [key, item] of Object.entries(parts)) {
            const option = document.createElement("option");
            option.value = key; option.textContent = item.title;
            byId("component-select").append(option);
        }
        byId("component-select").value = component;
        byId("component-select").onchange = event => choose(event.target.value);
        byId("view-transparent").onclick = () => mode(true);
        byId("view-exterior").onclick = () => mode(false);
        byId("shell-opacity").oninput = opacity;
        byId("motor-focus").onclick = () => {
            const focus = byId("stage").classList.toggle("motor-focus");
            byId("plant-svg").setAttribute("viewBox", focus ? "190 85 375 265" : "0 0 1000 460");
            byId("motor-focus").textContent = focus ? "↗ Ver conjunto" : "⌕ Acercar motor";
            byId("motor-focus").setAttribute("aria-pressed", String(focus));
        };
        reduced.addEventListener("change", () => {if (state) update(state);});
        document.addEventListener("visibilitychange", () => {if (state) update(state);});
        mode(true); highlight(); draw(0);
    }

    function opacity() {
        const value = Number(byId("shell-opacity").value);
        byId("stage").style.setProperty("--shell-opacity", value / 100);
        byId("shell-opacity-value").textContent = value + " %";
    }
    function mode(transparent) {
        shell = transparent;
        byId("stage").classList.toggle("transparent", shell);
        byId("view-transparent").setAttribute("aria-pressed", String(shell));
        byId("view-exterior").setAttribute("aria-pressed", String(!shell));
        byId("shell-opacity").disabled = !shell;
        opacity();
    }
    function choose(key) {
        if (!parts[key]) return;
        component = key;
        byId("component-select").value = key;
        highlight();
        if (selectZone) selectZone(parts[key].zone);
    }
    function highlight() {
        document.querySelectorAll("[data-part]").forEach(el => el.classList.toggle("part-selected", el.dataset.part === component));
        byId("component-title").textContent = parts[component].title;
        byId("component-description").textContent = parts[component].info;
    }
    function select(zone) {
        const mapped = zone === "casing" ? "casing" : zone;
        if (parts[mapped] && parts[component].zone !== zone) {
            component = mapped; byId("component-select").value = component; highlight();
        }
    }

    function show(id, value) {byId(id).style.opacity = clamp(value);}
    function update(s) {
        state = s;
        const fresh = !!s.current;
        const spinning = fresh && s.running && s.plant.context.rpm > 100;
        byId("mechanical-state").textContent = !fresh ? "◌ Sin datos actuales · animación detenida" : spinning ? (reduced.matches ? "○ Giro sin animación · movimiento reducido" : "↻ Giro ilustrativo · velocidad reducida") : "○ Motor detenido · sin giro";
        byId("mechanical-state").classList.toggle("unavailable", !fresh);
        byId("mechanical-effects").replaceChildren();
        const p = s.settings;
        const causes = [
            ["lubrication", p.lubrication_pct < 80, "Fricción · DE / NDE", "Contacto naranja en los rodamientos; el calor aumenta con retraso."],
            ["contamination", p.contamination_pct > 10, "Contaminación · DE / NDE", "Partículas ilustrativas en el lubricante; el agua permanece limpia."],
            ["bearing", p.bearing_defect_pct > 10, "Defecto impuesto · DE / NDE", "Marca ilustrativa de contacto e impulsos. No identifica una pista dañada real."],
            ["alignment", p.misalignment_mm > .15, "Desalineación · DE / acoplamiento", "Desplazamiento amplificado del eje de transmisión y carga dibujada en DE."],
            ["imbalance", p.imbalance_gmm > 30, "Desequilibrio · rotor / apoyos", "Masa excéntrica ilustrativa y mayor vibración a una vuelta."],
            ["looseness", p.looseness_pct > 10, "Fijación suelta · patas / carcasa", "Los pernos resaltados indican la holgura que has introducido."],
            ["cooling", p.cooling_pct < 70, "Refrigeración limitada · motor", "Menos líneas de aire. El rojo aparece al subir la temperatura superficial."],
            ["cavitation", s.plant.context.cavitation_index > .05, "Cavitación · bomba", "Burbujas ilustrativas en el impulsor; no es un defecto localizado del rotor."]
        ];
        for (const [key, on, title, info] of causes) {
            byId("stage").classList.toggle("cause-" + key, fresh && on);
            if (on && fresh) {
                const el = document.createElement("li");
                const strong = document.createElement("strong"); strong.textContent = "◇ " + title;
                const text = document.createElement("span"); text.textContent = info;
                el.append(strong, text); byId("mechanical-effects").append(el);
            }
        }
        if (!byId("mechanical-effects").children.length) {
            const el = document.createElement("li");
            el.textContent = fresh ? "✓ Sin causas adversas impuestas. El calor residual puede persistir mientras el equipo se enfría." : "Sin telemetría actual. Los ajustes se conservan; los efectos en vivo se reanudarán con un paquete nuevo.";
            byId("mechanical-effects").append(el);
        }
        const bearingZone = component === "nde" || component === "fan" ? "nde" : "de";
        const z = s.current?.zones[bearingZone];
        byId("detail-label").textContent = "RODAMIENTO " + bearingZone.toUpperCase();
        byId("detail-caption").textContent = "Detalle ampliado · " + bearingZone.toUpperCase() + " · geometría supuesta";
        byId("detail-signal").textContent = z ? z.temperature_c.toLocaleString("es-CL", {maximumFractionDigits: 1}) + " °C · " + z.vibration_rms_m_s2.toLocaleString("es-CL", {maximumFractionDigits: 2}) + " m/s²" : "— °C · — m/s² · sin datos actuales";
        byId("bearing-detail").classList.toggle("detail-vibrating", fresh && z.vibration_rms_m_s2 >= 3);
        byId("bearing-detail").classList.toggle("detail-unavailable", !fresh);
        show("detail-friction", fresh ? (100 - p.lubrication_pct) / 100 : 0);
        show("detail-dirt", fresh ? p.contamination_pct / 100 : 0);
        show("detail-defect", fresh ? p.bearing_defect_pct / 100 : 0);
        byId("detail-heat").style.setProperty("--heat", z ? clamp((z.temperature_c - 55) / 35) : 0);
        show("alignment-force", fresh ? p.misalignment_mm / 1.5 : 0);
        show("eccentric-mass", fresh ? p.imbalance_gmm / 400 : 0);
        show("pump-bubbles", fresh ? s.plant.context.cavitation_index : 0);
        byId("air-streams").style.opacity = fresh ? p.cooling_pct / 100 : 0;
        byId("motor-feet").style.setProperty("--shake", (fresh ? 4 * p.looseness_pct / 100 : 0) + "px");
        for (const el of document.querySelectorAll(".bearing-friction")) el.style.opacity = fresh ? (100 - p.lubrication_pct) / 100 : 0;
        for (const el of document.querySelectorAll(".bearing-dirt")) el.style.opacity = fresh ? p.contamination_pct / 100 : 0;
        for (const el of document.querySelectorAll(".bearing-defect")) el.style.opacity = fresh ? p.bearing_defect_pct / 100 : 0;
        active = spinning && !reduced.matches && !document.hidden;
        if (active && animationId === null) {previous = 0; animationId = requestAnimationFrame(animate);}
        if (!active && animationId !== null) {cancelAnimationFrame(animationId); animationId = null; previous = 0;}
        draw(angle);
    }

    function invalidate() {
        if (!state) return;
        update({...state, current: null});
    }
    function animate(now) {
        animationId = null;
        if (!active) return;
        const dt = previous ? Math.min(.06, (now - previous) / 1000) : 0;
        previous = now;
        // 0,55 vueltas de dibujo/s a velocidad nominal: evita aliasing y flashes.
        angle = (angle + dt * tau * .55 * Math.min(1, state.plant.context.rpm / 2910)) % (tau * 10);
        draw(angle);
        animationId = requestAnimationFrame(animate);
    }
    function draw(a) {
        rotating.bars.forEach((el, i) => {
            const t = a + i * tau / rotating.bars.length;
            const y1 = 217 + 25 * Math.sin(t), y2 = 217 + 25 * Math.sin(t + .23);
            el.setAttribute("d", `M326 ${y1}L454 ${y2}`);
            el.style.opacity = Math.cos(t) > 0 ? .78 : .14;
        });
        for (const {el, i, cx} of rotating.balls) {
            const t = a * .4 + i * tau / 8;
            el.setAttribute("cx", cx + 14 * Math.cos(t)); el.setAttribute("cy", 217 + 29 * Math.sin(t));
            el.style.opacity = .65 + .35 * (Math.cos(t) + 1) / 2;
        }
        rotating.detailBalls.forEach((el, i) => {
            const t = a * .4 + i * tau / rotating.detailBalls.length;
            el.setAttribute("cx", 95 + 43 * Math.cos(t)); el.setAttribute("cy", 88 + 43 * Math.sin(t));
        });
        rotating.fan.forEach((el, i) => {
            const t = a + i * tau / 6, x = 240 + 12 * Math.cos(t), y = 217 + 44 * Math.sin(t);
            el.setAttribute("d", `M240 217Q${x+7} ${y} ${x} ${y}L${x-4} ${y-5}Z`);
        });
        byId("eccentric-mass").setAttribute("cy", 217 + 24 * Math.sin(a));
        byId("eccentric-mass").style.visibility = Math.cos(a) >= -.2 ? "visible" : "hidden";
        const amp = state?.current ? state.settings.imbalance_gmm / 400 * 1.7 : 0;
        byId("rotor-body").setAttribute("transform", `translate(0 ${active ? amp * Math.sin(a) : 0})`);
    }
    return {init, update, invalidate, select};
})();
