#!/usr/bin/env python3
"""Generate DaVinci Resolve presets for Ram's Video Effects: Fusion templates (.setting -> .drfx) + LUTs (.cube)."""
import os, zipfile, numpy as np

INK = (0.08, 0.08, 0.08); YEL = (1.0, 0.878, 0.227); PAPER = (0.937, 0.91, 0.847); WHITE = (1, 1, 1); RED = (0.886, 0.216, 0.169)

def L(v):
    """python -> Fusion lua literal"""
    if isinstance(v, bool): return "true" if v else "false"
    if isinstance(v, (int, float)): return repr(round(float(v), 5)) if isinstance(v, float) else str(v)
    if isinstance(v, str): return '"' + v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
    if isinstance(v, (list, tuple)): return "{ " + ", ".join(L(x) for x in v) + " }"
    raise TypeError(v)

def inp(value=None, expr=None, src=None):
    if src: return f'Input {{ SourceOp = "{src[0]}", Source = "{src[1]}", }}'
    parts = []
    if value is not None: parts.append(f"Value = {L(value)}")
    if expr: parts.append(f"Expression = {L(expr)}")
    return "Input { " + ", ".join(parts) + ", }"

def tool(kind, inputs, extra=""):
    body = "\n".join(f"\t\t\t\t\t{k} = {v}," for k, v in inputs.items())
    return f"{kind} {{\n\t\t\t\tInputs = {{\n{body}\n\t\t\t\t}},{extra}\n\t\t\t}}"

FF = {"UseFrameFormatSettings": inp(1), "Width": inp(1920), "Height": inp(1080)}

def bg(color, alpha=1.0):
    d = dict(FF); d.update({"TopLeftRed": inp(color[0]), "TopLeftGreen": inp(color[1]), "TopLeftBlue": inp(color[2]), "TopLeftAlpha": inp(alpha)})
    return d

def rect(cx, cy, w, h, radius=0.0, soft=0.0, angle=0.0, center_expr=None, width_expr=None, border=None):
    d = {"MaskWidth": inp(1920), "MaskHeight": inp(1080), "UseFrameFormatSettings": inp(1),
         "Center": inp([cx, cy], center_expr), "Width": inp(w, width_expr), "Height": inp(h), "CornerRadius": inp(radius), "SoftEdge": inp(soft)}
    if angle: d["Angle"] = inp(angle)
    if border: d["BorderWidth"] = inp(border); d["Solid"] = inp(0)
    return d

def text(txt, size, color, font="Arial", style="Bold", cx=0.5, cy=0.5, hj=1, center_expr=None, extra=None):
    d = dict(FF); d.update({"StyledText": inp(txt), "Font": inp(font), "Style": inp(style), "Size": inp(size),
         "VerticalJustificationNew": inp(3), "HorizontalJustificationNew": inp(hj),  # 0 left 1 centre 2 right ; 3 = centre
         "Center": inp([cx, cy], center_expr), "Red1": inp(color[0]), "Green1": inp(color[1]), "Blue1": inp(color[2])})
    if extra: d.update(extra)
    return d

def merge(bgsrc, fgsrc, extra=None):
    d = {"Background": inp(src=(bgsrc, "Output")), "Foreground": inp(src=(fgsrc, "Output")), "PerformDepthMerge": inp(0)}
    if extra: d.update(extra)
    return d

def macro(name, tools, out, published, inputs_main=None, kind="title"):
    """tools: list of (toolname, kind, inputs dict, maskSource or None). published: list of (label, tool, input)"""
    lines = []
    for tn, tk, ti, mask in tools:
        ti = dict(ti)
        if mask: ti["EffectMask"] = inp(src=(mask, "Mask"))
        lines.append(f"\t\t\t{tn} = " + tool(tk, ti) + ",")
    ins = []
    for i, (src_tool, src_inp) in enumerate(inputs_main or [], 1):
        ins.append(f'\t\t\t\tMainInput{i} = InstanceInput {{ SourceOp = "{src_tool}", Source = "{src_inp}", }},')
    for i, (label, tn, ti) in enumerate(published, 1):
        ins.append(f'\t\t\t\tInput{i} = InstanceInput {{ SourceOp = "{tn}", Source = "{ti}", Name = {L(label)}, }},')
    return f'''{{
	Tools = ordered() {{
		{name} = MacroOperator {{
			CtrlWZoom = false,
			NameSet = true,
			Inputs = ordered() {{
{chr(10).join(ins)}
			}},
			Outputs = {{
				MainOutput1 = InstanceOutput {{ SourceOp = "{out}", Source = "Output", }},
			}},
			ViewInfo = GroupInfo {{ Pos = {{ 0, 0 }}, }},
			Tools = ordered() {{
{chr(10).join(lines)}
			}},
		}},
	}},
	ActiveTool = "{name}",
}}
'''

E3 = lambda f: f"(1-min(time/{f},1))*(1-min(time/{f},1))*(1-min(time/{f},1))"   # ease-out cubic remaining (1 -> 0)

T = {}
# ---------------------------------------------------------------- TITLES
T["Titles/RVE Torn Headline"] = macro("RVE_TornHeadline", [
    ("Clear", "Background", bg((0, 0, 0), 0.0), None),
    ("StripMask", "RectangleMask", rect(0.5, 0.86, 1.15, 0.2, soft=0.004, angle=-1.5, center_expr=f"Point(0.5-1.2*{E3(14)}, 0.86)"), None),
    ("Paper", "FastNoise", dict(FF, Detail=inp(6.0), XScale=inp(18.0), Contrast=inp(0.25), Brightness=inp(0.0),
        Color1Red=inp(0.88), Color1Green=inp(0.85), Color1Blue=inp(0.79), Color2Red=inp(0.97), Color2Green=inp(0.95), Color2Blue=inp(0.9)), "StripMask"),
    ("Strip", "Merge", merge("Clear", "Paper"), None),
    ("KickerMask", "RectangleMask", rect(0.17, 0.915, 0.17, 0.045, center_expr=f"Point(0.17-1.2*{E3(14)}, 0.915)"), None),
    ("KickerBox", "Background", bg(YEL), "KickerMask"),
    ("WithKicker", "Merge", merge("Strip", "KickerBox"), None),
    ("Kicker", "TextPlus", text("EXPLAINED", 0.03, INK, "Courier New", "Bold", 0.17, 0.915, center_expr=f"Point(0.17-1.2*{E3(14)}, 0.915)"), None),
    ("WithKickerText", "Merge", merge("WithKicker", "Kicker"), None),
    ("Headline", "TextPlus", text("Why everyone is talking about this", 0.06, INK, "Arial Black", "Regular", 0.09, 0.84, hj=0, center_expr=f"Point(0.09-1.2*{E3(14)}, 0.84)"), None),
    ("Out", "Merge", merge("WithKickerText", "Headline"), None)],
    "Out", [("Kicker", "Kicker", "StyledText"), ("Headline", "Headline", "StyledText"), ("Headline Font", "Headline", "Font"), ("Headline Size", "Headline", "Size")])

T["Titles/RVE Marker Text"] = macro("RVE_MarkerText", [
    ("Clear", "Background", bg((0, 0, 0), 0.0), None),
    ("StripMask", "RectangleMask", rect(0.5, 0.25, 0.62, 0.12, soft=0.003, angle=1.2, center_expr=f"Point(0.5-1.2*{E3(12)}, 0.25)"), None),
    ("Strip", "Background", bg((0.98, 0.97, 0.94)), "StripMask"),
    ("S1", "Merge", merge("Clear", "Strip"), None),
    ("HiMask", "RectangleMask", rect(0.5, 0.245, 0.56, 0.075, angle=1.2, width_expr="0.56*min(max((time-10)/14,0),1)",
        center_expr="Point(0.22+0.28*min(max((time-10)/14,0),1), 0.245)"), None),
    ("Highlight", "Background", bg(YEL, 0.92), "HiMask"),
    ("S2", "Merge", merge("S1", "Highlight"), None),
    ("Words", "TextPlus", text("This is the real reason", 0.065, INK, "Arial Black", "Regular", 0.5, 0.25, center_expr=f"Point(0.5-1.2*{E3(12)}, 0.25)"), None),
    ("Out", "Merge", merge("S2", "Words"), None)],
    "Out", [("Text", "Words", "StyledText"), ("Font", "Words", "Font"), ("Size", "Words", "Size"),
            ("Strip Width", "StripMask", "Width"), ("Highlight Width", "HiMask", "Width"), ("Highlight Color", "Highlight", "TopLeftRed")])

T["Titles/RVE Context Label"] = macro("RVE_ContextLabel", [
    ("Clear", "Background", bg((0, 0, 0), 0.0), None),
    ("BarMask", "RectangleMask", rect(0.06, 0.14, 0.008, 0.07), None),
    ("Bar", "Background", bg(YEL), "BarMask"),
    ("S1", "Merge", merge("Clear", "Bar"), None),
    ("BoxMask", "RectangleMask", rect(0.2, 0.14, 0.26, 0.07, width_expr="0.26*min(time/20,1)", center_expr="Point(0.067+0.13*min(time/20,1), 0.14)"), None),
    ("Box", "Background", bg(INK, 0.92), "BoxMask"),
    ("S2", "Merge", merge("S1", "Box"), None),
    ("Label", "TextPlus", text("KATHMANDU, 2026", 0.04, WHITE, "Courier New", "Bold", 0.075, 0.14, hj=0, extra={"WriteOnEnd": inp(1.0, "min(time/28,1)")}), None),
    ("Out", "Merge", merge("S2", "Label"), None)],
    "Out", [("Label", "Label", "StyledText"), ("Box Width", "BoxMask", "Width")])

T["Titles/RVE Source Tag"] = macro("RVE_SourceTag", [
    ("Clear", "Background", bg((0, 0, 0), 0.0), None),
    ("ChipMask", "RectangleMask", rect(0.85, 0.05, 0.26, 0.045, radius=0.0), None),
    ("Chip", "Background", bg((0.97, 0.95, 0.92), 0.92), "ChipMask"),
    ("S1", "Merge", merge("Clear", "Chip"), None),
    ("Src", "TextPlus", text("Source: World Bank, 2024", 0.022, INK, "Courier New", "Bold", 0.85, 0.05), None),
    ("Out", "Merge", merge("S1", "Src", {"Blend": inp(1.0, "min(time/10,1)")}), None)],
    "Out", [("Source", "Src", "StyledText"), ("Chip Width", "ChipMask", "Width"), ("Chip Center", "ChipMask", "Center")])

T["Titles/RVE Big Number"] = macro("RVE_BigNumber", [
    ("Clear", "Background", bg((0, 0, 0), 0.0), None),
    ("CardMask", "RectangleMask", rect(0.5, 0.5, 0.5, 0.32, soft=0.002), None),
    ("Card", "FastNoise", dict(FF, Detail=inp(6.0), XScale=inp(18.0), Contrast=inp(0.2), Color1Red=inp(0.9), Color1Green=inp(0.88), Color1Blue=inp(0.82),
        Color2Red=inp(0.98), Color2Green=inp(0.96), Color2Blue=inp(0.92)), "CardMask"),
    ("S1", "Merge", merge("Clear", "Card", {"Size": inp(1.0, "0.85+0.15*min(time/8,1)")}), None),
    ("UnderMask", "RectangleMask", rect(0.5, 0.43, 0.3, 0.012, width_expr="0.3*min(max((time-8)/12,0),1)"), None),
    ("Under", "Background", bg(YEL), "UnderMask"),
    ("S2", "Merge", merge("S1", "Under"), None),
    ("Number", "TextPlus", text("3,000,000", 0.12, INK, "Arial Black", "Regular", 0.5, 0.53, extra={"Size": inp(0.12, "0.12*(0.85+0.15*min(time/8,1))")}), None),
    ("S3", "Merge", merge("S2", "Number"), None),
    ("Label", "TextPlus", text("people work abroad", 0.035, (0.2, 0.2, 0.2), "Arial", "Bold", 0.5, 0.39), None),
    ("Out", "Merge", merge("S3", "Label"), None)],
    "Out", [("Number", "Number", "StyledText"), ("Label", "Label", "StyledText"), ("Card Width", "CardMask", "Width"), ("Card Center", "CardMask", "Center")])

T["Titles/RVE Sticker"] = macro("RVE_Sticker", [
    ("Clear", "Background", bg((0, 0, 0), 0.0), None),
    ("StMask", "RectangleMask", rect(0.75, 0.82, 0.2, 0.09, radius=0.15, angle=8), None),
    ("St", "Background", bg(YEL), "StMask"),
    ("S1", "Merge", merge("Clear", "St"), None),
    ("Word", "TextPlus", text("NEW!", 0.06, INK, "Arial Black", "Regular", 0.75, 0.82, extra={"Angle": inp(8.0)}), None),
    ("S2", "Merge", merge("S1", "Word"), None),
    ("Pop", "Transform", {"Input": inp(src=("S2", "Output")), "Pivot": inp([0.75, 0.82]), "Center": inp([0.5, 0.5]),
        "Size": inp(1.0, "iif(time<6, 1.2*time/6, iif(time<10, 1.2-0.2*(time-6)/4, 1))")}, None)],
    "Pop", [("Text", "Word", "StyledText"), ("Sticker Center", "StMask", "Center"), ("Text Center", "Word", "Center"), ("Angle", "StMask", "Angle")])

T["Titles/RVE Name Tag"] = macro("RVE_NameTag", [
    ("Clear", "Background", bg((0, 0, 0), 0.0), None),
    ("NMask", "RectangleMask", rect(0.2, 0.2, 0.3, 0.075, width_expr="0.3*min(time/12,1)", center_expr="Point(0.05+0.15*min(time/12,1), 0.2)"), None),
    ("NBox", "Background", bg(INK, 0.92), "NMask"),
    ("S1", "Merge", merge("Clear", "NBox"), None),
    ("TMask", "RectangleMask", rect(0.13, 0.145, 0.16, 0.045, width_expr="0.16*min(max((time-6)/12,0),1)", center_expr="Point(0.05+0.08*min(max((time-6)/12,0),1), 0.145)"), None),
    ("TBox", "Background", bg(YEL), "TMask"),
    ("S2", "Merge", merge("S1", "TBox"), None),
    ("Name", "TextPlus", text("Your Name", 0.045, WHITE, "Arial Black", "Regular", 0.065, 0.2, hj=0, extra={"WriteOnEnd": inp(1.0, "min(time/16,1)")}), None),
    ("S3", "Merge", merge("S2", "Name"), None),
    ("Role", "TextPlus", text("Digital marketer", 0.026, INK, "Courier New", "Bold", 0.06, 0.145, hj=0, extra={"WriteOnEnd": inp(1.0, "min(max((time-8)/16,0),1)")}), None),
    ("Out", "Merge", merge("S3", "Role"), None)],
    "Out", [("Name", "Name", "StyledText"), ("Title", "Role", "StyledText"), ("Name Box Width", "NMask", "Width")])

T["Titles/RVE Progress Bar"] = macro("RVE_ProgressBar", [
    ("Clear", "Background", bg((0, 0, 0), 0.0), None),
    ("PMask", "RectangleMask", rect(0.5, 0.995, 1.0, 0.012, width_expr="time/max(comp.RenderEnd,1)", center_expr="Point(0.5*time/max(comp.RenderEnd,1), 0.995)"), None),
    ("Bar", "Background", bg(YEL), "PMask"),
    ("Out", "Merge", merge("Clear", "Bar"), None)],
    "Out", [("Color Red", "Bar", "TopLeftRed"), ("Color Green", "Bar", "TopLeftGreen"), ("Color Blue", "Bar", "TopLeftBlue"), ("Thickness", "PMask", "Height")])

# ---------------------------------------------------------------- EFFECT (needs the clip under it)
T["Effects/RVE Glass Card"] = macro("RVE_GlassCard", [
    ("In", "PipeRouter", {}, None),
    ("CardMask", "RectangleMask", rect(0.75, 0.62, 0.32, 0.26, radius=0.18, soft=0.0), None),
    ("Frost", "Blur", {"Input": inp(src=("In", "Output")), "XBlurSize": inp(40.0)}, "CardMask"),
    ("Lift", "BrightnessContrast", {"Input": inp(src=("Frost", "Output")), "Gain": inp(1.12), "Saturation": inp(1.15)}, "CardMask"),
    ("TintMask", "RectangleMask", rect(0.75, 0.62, 0.32, 0.26, radius=0.18), None),
    ("Tint", "Background", bg(WHITE, 0.14), "TintMask"),
    ("S1", "Merge", merge("Lift", "Tint"), None),
    ("EdgeMask", "RectangleMask", rect(0.75, 0.62, 0.32, 0.26, radius=0.18, border=0.003), None),
    ("Edge", "Background", bg(WHITE, 0.55), "EdgeMask"),
    ("S2", "Merge", merge("S1", "Edge"), None),
    ("Title", "TextPlus", text("Followers", 0.028, WHITE, "Arial", "Bold", 0.64, 0.705, hj=0), None),
    ("S3", "Merge", merge("S2", "Title"), None),
    ("Value", "TextPlus", text("12.4K", 0.075, WHITE, "Arial Black", "Regular", 0.64, 0.6, hj=0), None),
    ("Out", "Merge", merge("S3", "Value", {"Blend": inp(1.0, "min(time/10,1)")}), None)],
    "Out", [("Title", "Title", "StyledText"), ("Value", "Value", "StyledText"), ("Card Center", "CardMask", "Center"),
            ("Card Width", "CardMask", "Width"), ("Card Height", "CardMask", "Height"), ("Frost", "Frost", "XBlurSize"),
            ("Title Position", "Title", "Center"), ("Value Position", "Value", "Center")],
    inputs_main=[("In", "Input")])
# keep the other masks in step with the card: expressions follow CardMask
T["Effects/RVE Glass Card"] = (T["Effects/RVE Glass Card"]
    .replace('Center = Input { Value = { 0.75, 0.62 }, },\n\t\t\t\t\tWidth = Input { Value = 0.32, },\n\t\t\t\t\tHeight = Input { Value = 0.26, },\n\t\t\t\t\tCornerRadius = Input { Value = 0.18, },\n\t\t\t\t\tSoftEdge = Input { Value = 0.0, },\n\t\t\t\t\tBorderWidth',
             'Center = Input { Value = { 0.75, 0.62 }, Expression = "CardMask.Center", },\n\t\t\t\t\tWidth = Input { Value = 0.32, Expression = "CardMask.Width", },\n\t\t\t\t\tHeight = Input { Value = 0.26, Expression = "CardMask.Height", },\n\t\t\t\t\tCornerRadius = Input { Value = 0.18, },\n\t\t\t\t\tSoftEdge = Input { Value = 0.0, },\n\t\t\t\t\tBorderWidth'))
gc = T["Effects/RVE Glass Card"]; i = gc.index("TintMask = RectangleMask"); j = gc.index("Tint = Background")
gc = gc[:i] + gc[i:j].replace('Center = Input { Value = { 0.75, 0.62 }, },', 'Center = Input { Value = { 0.75, 0.62 }, Expression = "CardMask.Center", },') \
    .replace('Width = Input { Value = 0.32, },', 'Width = Input { Value = 0.32, Expression = "CardMask.Width", },') \
    .replace('Height = Input { Value = 0.26, },', 'Height = Input { Value = 0.26, Expression = "CardMask.Height", },') + gc[j:]
T["Effects/RVE Glass Card"] = gc

# ---------------------------------------------------------------- TRANSITION
P = "min(max(time/max(comp.RenderEnd,1),0),1)"
T["Transitions/RVE Block Wipe"] = macro("RVE_BlockWipe", [
    ("Outgoing", "PipeRouter", {}, None),
    ("Incoming", "PipeRouter", {}, None),
    ("Cut", "Dissolve", {"Background": inp(src=("Outgoing", "Output")), "Foreground": inp(src=("Incoming", "Output")), "Mix": inp(0.0, f"iif({P}<0.5,0,1)")}, None),
    ("YMask", "RectangleMask", rect(0.5, 0.5, 1.0, 1.2, center_expr=f"Point(-0.55+2.1*{P}, 0.5)"), None),
    ("Yellow", "Background", bg(YEL), "YMask"),
    ("S1", "Merge", merge("Cut", "Yellow"), None),
    ("BMask", "RectangleMask", rect(0.5, 0.5, 1.0, 1.2, center_expr=f"Point(-0.55+2.1*max({P}-0.12,0)/0.88, 0.5)"), None),
    ("Black", "Background", bg(INK), "BMask"),
    ("Out", "Merge", merge("S1", "Black"), None)],
    "Out", [("Block 1 Red", "Yellow", "TopLeftRed"), ("Block 1 Green", "Yellow", "TopLeftGreen"), ("Block 1 Blue", "Yellow", "TopLeftBlue")],
    inputs_main=[("Outgoing", "Input"), ("Incoming", "Input")])

# ---------------------------------------------------------------- GENERATOR
T["Generators/RVE Paper Background"] = macro("RVE_PaperBackground", [
    ("Paper", "FastNoise", dict(FF, Detail=inp(7.0), XScale=inp(14.0), Contrast=inp(0.22), Brightness=inp(0.0),
        Color1Red=inp(0.87), Color1Green=inp(0.84), Color1Blue=inp(0.77), Color2Red=inp(0.96), Color2Green=inp(0.94), Color2Blue=inp(0.88),
        SeetheRate=inp(0.02)), None),
    ("Vignette", "EllipseMask", {"MaskWidth": inp(1920), "MaskHeight": inp(1080), "UseFrameFormatSettings": inp(1), "Width": inp(1.5), "Height": inp(1.5),
        "SoftEdge": inp(0.5), "Invert": inp(1)}, None),
    ("Dark", "Background", bg((0.25, 0.2, 0.12), 0.25), "Vignette"),
    ("Out", "Merge", merge("Paper", "Dark"), None)],
    "Out", [("Light Red", "Paper", "Color2Red"), ("Light Green", "Paper", "Color2Green"), ("Light Blue", "Paper", "Color2Blue"), ("Grain Size", "Paper", "XScale")])

# ---------------------------------------------------------------- LUTs
def lut(fn, path, n=33):
    g = np.linspace(0, 1, n); out = [f'TITLE "{os.path.basename(path)[:-5]}"', f"LUT_3D_SIZE {n}", "DOMAIN_MIN 0 0 0", "DOMAIN_MAX 1 1 1"]
    for b in g:
        for gg in g:
            for r in g:
                c = np.clip(fn(np.array([r, gg, b])), 0, 1); out.append(f"{c[0]:.6f} {c[1]:.6f} {c[2]:.6f}")
    open(path, "w").write("\n".join(out) + "\n")

luma = lambda c: c @ np.array([0.299, 0.587, 0.114])
def sat(c, s): y = luma(c); return y + (c - y) * s
def contrast(c, k, p=0.5): return (c - p) * k + p
def scurve(c, k=0.6): return c + k * c * (1 - c) * (c - 0.5) * 2 * 0.5
LUTS = {
    "RVE Paper Warm": lambda c: contrast(sat(c * np.array([1.04, 1.0, 0.9]), 0.82), 1.05) * 0.96 + 0.03,
    "RVE Archive Sepia": lambda c: (contrast(luma(c), 1.25) * np.array([1.07, 0.93, 0.74]) + np.array([0.04, 0.02, -0.01])) * 0.92 + 0.04,
    "RVE Archive BW": lambda c: np.repeat(contrast(luma(c), 1.3), 3) * 0.9 + 0.05,
    "RVE Moody": lambda c: (lambda y: sat(contrast(c, 1.12) * 0.88 + (1 - y) * np.array([-0.02, 0.02, 0.05]) + y * np.array([0.05, 0.015, -0.03]), 0.78))(luma(c)),
    "RVE Red Film": lambda c: contrast(sat(c, 0.6) * np.array([1.18, 0.72, 0.7]), 1.15) + np.array([0.04, 0.0, 0.0]),
    "RVE Pastel": lambda c: sat(c, 0.75) * 0.82 + np.array([0.13, 0.11, 0.17]),
    "RVE Punchy Reel": lambda c: sat(scurve(c, 0.8), 1.25),
}

def build(dst):
    os.makedirs(dst, exist_ok=True)
    with zipfile.ZipFile(os.path.join(dst, "RamVideoEffects.drfx"), "w", zipfile.ZIP_DEFLATED) as z:
        for k, v in T.items():
            kind, nm = k.split("/")
            z.writestr(f"Edit/{kind}/Ram Video Effects/{nm}.setting", v)
    os.makedirs(os.path.join(dst, "settings"), exist_ok=True)
    for k, v in T.items():
        kind, nm = k.split("/"); d = os.path.join(dst, "settings", kind); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, nm + ".setting"), "w").write(v)
    os.makedirs(os.path.join(dst, "LUTs", "Ram Video Effects"), exist_ok=True)
    for nm, fn in LUTS.items(): lut(fn, os.path.join(dst, "LUTs", "Ram Video Effects", nm + ".cube"))

if __name__ == "__main__":
    build(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out"))
    print(len(T), "templates,", len(LUTS), "LUTs")
