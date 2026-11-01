#!/usr/bin/env python3
"""Generate the BeagleBone Black bring-up diagrams as light/dark SVG pairs.

    python3 tools/bbb_diagrams.py

Writes docs/assets/bbb/<name>-<lang>-<light|dark>.svg. Reference both in Markdown
so the image follows the site's theme toggle (see src/css/custom.css):

    ![alt](../assets/bbb/boot-chain-zh-light.svg#gh-light-mode-only)
    ![alt](../assets/bbb/boot-chain-zh-dark.svg#gh-dark-mode-only)

Edit the text here and re-run; don't hand-edit the generated SVGs.
"""
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "docs" / "assets" / "bbb"
W = 680
FONT = ("system-ui, -apple-system, 'Segoe UI', 'Noto Sans TC', 'PingFang TC', "
        "'Microsoft JhengHei', sans-serif")

# fill, stroke, title, subtitle — from one ramp per role so light/dark stay paired
PALETTE = {
    "light": {
        "purple": ("#EEEDFE", "#534AB7", "#3C3489", "#534AB7"),
        "amber": ("#FAEEDA", "#854F0B", "#633806", "#854F0B"),
        "teal": ("#E1F5EE", "#0F6E56", "#085041", "#0F6E56"),
        "gray": ("#F1EFE8", "#5F5E5A", "#444441", "#5F5E5A"),
        "line": "#73726C",
        "muted": "#5F5E5A",
    },
    "dark": {
        "purple": ("#3C3489", "#AFA9EC", "#EEEDFE", "#CECBF6"),
        "amber": ("#633806", "#EF9F27", "#FAEEDA", "#FAC775"),
        "teal": ("#085041", "#5DCAA5", "#E1F5EE", "#9FE1CB"),
        "gray": ("#444441", "#B4B2A9", "#F1EFE8", "#D3D1C7"),
        "line": "#9C9A92",
        "muted": "#B4B2A9",
    },
}


class Svg:
    def __init__(self, height, title, desc, mode):
        self.p = PALETTE[mode]
        self.h = height
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" '
            f'width="{W}" height="{height}" role="img" font-family="{escape(FONT)}">',
            f"<title>{escape(title)}</title><desc>{escape(desc)}</desc>",
            '<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" '
            'markerHeight="6" orient="auto-start-reverse"><path d="M2 1L8 5L2 9" fill="none" '
            f'stroke="{self.p["line"]}" stroke-width="1.5" stroke-linecap="round" '
            'stroke-linejoin="round"/></marker></defs>',
        ]

    def box(self, x, y, w, h, ramp, title, sub=None, title_size=14):
        fill, stroke, tc, sc = self.p[ramp]
        cx = x + w / 2
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" '
                          f'fill="{fill}" stroke="{stroke}" stroke-width="0.75"/>')
        if sub is None:
            self._text(cx, y + h / 2, title, tc, title_size, 500, "middle")
            return
        lines = (sub,) if isinstance(sub, str) else sub
        top = y + h / 2 - 9 * len(lines)
        self._text(cx, top, title, tc, title_size, 500, "middle")
        for i, line in enumerate(lines):
            self._text(cx, top + 19 + 17 * i, line, sc, 12, 400, "middle")

    def region(self, x, y, w, h, ramp, title, sub=None):
        """A tinted, dashed frame marking a memory region, labelled at its top-left."""
        fill, stroke, tc, sc = self.p[ramp]
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" '
                          f'fill="{fill}" fill-opacity="0.45" stroke="{stroke}" '
                          'stroke-width="0.75" stroke-dasharray="4 3"/>')
        self._text(x + 12, y + 16, title, tc, 13, 600, "start")
        if sub:
            self._text(x + 12, y + 33, sub, sc, 11, 400, "start")

    def text(self, x, y, s, size=12, anchor="start", color=None):
        self._text(x, y, s, color or self.p["muted"], size, 400, anchor)

    def _text(self, x, y, s, color, size, weight, anchor):
        self.parts.append(f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
                          f'font-weight="{weight}" text-anchor="{anchor}" '
                          f'dominant-baseline="central">{escape(s)}</text>')

    def arrow(self, x1, y1, x2, y2):
        self.parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                          f'stroke="{self.p["line"]}" stroke-width="1" marker-end="url(#arrow)"/>')

    def leader(self, x1, y1, x2, y2):
        self.parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                          f'stroke="{self.p["line"]}" stroke-width="0.75" stroke-dasharray="3 3"/>')

    def swatch(self, x, y, ramp, label):
        fill, stroke, _, _ = self.p[ramp]
        self.parts.append(f'<rect x="{x}" y="{y - 7}" width="14" height="14" rx="3" '
                          f'fill="{fill}" stroke="{stroke}" stroke-width="0.75"/>')
        self.text(x + 22, y, label)

    def render(self):
        return "\n".join(self.parts + ["</svg>"]) + "\n"


TEXT = {
    "boot-chain": {
        "zh": {
            "title": "BeagleBone Black 開機鏈與這次踩到的坑",
            "desc": "由上而下五層：Boot ROM、SPL、U-Boot、Linux kernel、systemd 與 userspace，"
                    "每層右側是觀察點或這次遇到的問題。",
            "stages": [
                ("Boot ROM", "晶片內建，讀 SYSBOOT 找 MLO", "gray", "按住 S2 會改變開機順序"),
                ("SPL（MLO）", "在內部 SRAM 跑，初始化 DDR", "amber", "log 被 USB hub 重新列舉吃掉"),
                ("U-Boot", "env、bootcmd、tftp、bootz", "amber", "bootdelay=0，要狂送空白才攔得住"),
                ("Linux kernel", "解壓、讀 DTB、probe 驅動", "gray", "驗 Linux version 與 cmdline"),
                ("systemd 與 userspace", "掛 rootfs、起網路、login", "amber", "少了 net.ifnames=0，網卡變 end0"),
            ],
            "legend": ("這次實際踩到的坑", "觀察點與驗證方式"),
        },
        "en": {
            "title": "BeagleBone Black boot chain and where the pitfalls landed",
            "desc": "Five stages top to bottom: Boot ROM, SPL, U-Boot, Linux kernel, systemd and "
                    "userspace, each annotated with what to check or what went wrong.",
            "stages": [
                ("Boot ROM", "On-chip; reads SYSBOOT, finds MLO", "gray", "Holding S2 changes boot order"),
                ("SPL (MLO)", "Runs in SRAM, sets up DDR", "amber", "Log lost to USB hub re-enumeration"),
                ("U-Boot", "env, bootcmd, tftp, bootz", "amber", "bootdelay=0: must spam spaces"),
                ("Linux kernel", "Decompress, read DTB, probe", "gray", "Check Linux version and cmdline"),
                ("systemd and userspace", "Mount rootfs, network, login", "amber", "No net.ifnames=0: NIC is end0"),
            ],
            "legend": ("Pitfalls hit this time", "What to check"),
        },
    },
    "bootz-memory": {
        "zh": {
            "title": "bootz 前後的 DRAM 配置",
            "desc": "512 MiB DRAM 從 0x80000000 到 0xA0000000，由上而下為 U-Boot 本體、bootz 搬移後的 "
                    "DTB 與 initrd、initrd、DTB、zImage、kernel 解壓位置。不按比例。",
            "top": "DRAM 頂端（512 MiB）",
            "rows": [
                ("0x9FF59000", "gray", "U-Boot 本體（relocate 後）", None),
                ("0x8F5D2000", "teal", "DTB + initrd（bootz 搬過來）", "交給 kernel 的是這裡，r2 = DTB"),
                ("0x88080000", "purple", "initrd（rdaddr，10.5 MB）", None),
                ("0x88000000", "purple", "DTB（fdtaddr，約 99 KB）", None),
                ("0x82000000", "purple", "zImage（loadaddr，5.7 MB）", "offset 0x24 = 016f2818"),
                ("0x80008000", "teal", "kernel 解壓到這裡", None),
            ],
            "legend": ("tftp / load 放的位置", "之後被搬去的位置（不按比例）"),
        },
        "en": {
            "title": "DRAM layout around bootz",
            "desc": "512 MiB of DRAM from 0x80000000 to 0xA0000000; top to bottom: U-Boot itself, "
                    "DTB and initrd moved by bootz, initrd, DTB, zImage, and where the kernel "
                    "decompresses. Not to scale.",
            "top": "Top of DRAM (512 MiB)",
            "rows": [
                ("0x9FF59000", "gray", "U-Boot itself (relocated)", None),
                ("0x8F5D2000", "teal", "DTB + initrd (moved by bootz)", "What the kernel gets; r2 = DTB"),
                ("0x88080000", "purple", "initrd (rdaddr, 10.5 MB)", None),
                ("0x88000000", "purple", "DTB (fdtaddr, ~99 KB)", None),
                ("0x82000000", "purple", "zImage (loadaddr, 5.7 MB)", "offset 0x24 = 016f2818"),
                ("0x80008000", "teal", "Kernel decompresses here", None),
            ],
            "legend": ("Where tftp / load puts it", "Where it gets moved (not to scale)"),
        },
    },
    "gpio-led": {
        "zh": {
            "title": "讓 GPIO 點亮 LED 的四個步驟",
            "desc": "時脈、pinmux、方向 OE、輸出值四個步驟，下方是在 U-Boot 實際讀到的數值，"
                    "其中 OE 一開始全是輸入。",
            "steps": [
                ("時脈", "GPIO1_CLKCTRL", "teal", "讀到 0x2", "已開啟"),
                ("Pinmux", "conf_gpmc_a5..a8", "teal", "讀到 0x27", "mode 7 = GPIO"),
                ("方向", "GPIO_OE", "amber", "0xffffffff", "全是輸入，要清 0"),
                ("輸出值", "SET/CLEARDATAOUT", "teal", "寫 0x01e00000", "bit 21–24，四顆亮"),
            ],
            "note": "Linux 的 gpio-omap 驅動和 DTS 裡的 pinctrl、gpio-leds，做的就是這四步",
        },
    },
    "boot-memory-flow": {
        "zh": {
            "title": "開機每一段跑在哪、把誰搬去哪",
            "desc": "三條直欄是三個地方：內部 SRAM、DRAM、SD 卡或網路。五個步驟由上而下："
                    "Boot ROM 把 MLO 從 SD 複製進 SRAM；SPL 在 SRAM 裡初始化 DDR，再把 u-boot.img 搬進 DRAM；"
                    "U-Boot 在 DRAM 裡把自己搬到頂端；U-Boot 把 zImage、DTB、initrd 放進 DRAM，bootz 再搬一次；"
                    "zImage 在 DRAM 裡把 kernel 解壓到 0x80008000。",
            "lanes": {
                "sram": ("amber", "內部 SRAM", "晶片內，約 109 KB"),
                "dram": ("purple", "DRAM（外部 DDR3）", "0x80000000 起，512 MiB"),
                "sd": ("gray", "SD 卡 / 網路", "還沒進記憶體"),
            },
            # (步驟, 程式跑在哪, [(欄, 標題, 說明)], 箭頭 (從, 到) 或 None, 箭頭上的字)
            "steps": [
                ("① Boot ROM", "跑在晶片內 ROM",
                 [("sram", "SPL", "0x402F0400"), ("sd", "MLO", "FAT 分割區")],
                 ("sd", "sram"), "ROM 複製（DDR 還不能用）"),
                ("② SPL", "跑在 SRAM",
                 [("sram", "SPL 執行中", "初始化 DDR"), ("dram", "u-boot.img", "0x80800000"),
                  ("sd", "u-boot.img", "FAT 分割區")],
                 ("sd", "dram"), None),
                ("③ U-Boot", "跑在 DRAM",
                 [("dram", "U-Boot 搬自己到頂端", "0x80800000 → 0x9FF59000")], None, None),
                ("④ load + bootz", "U-Boot 執行",
                 [("dram", "zImage / DTB / initrd",
                   ("load 放到 0x82000000 起", "bootz 再搬到 0x8F5D2000")),
                  ("sd", "3 個檔", "ext4 或 TFTP")],
                 ("sd", "dram"), None),
                ("⑤ zImage", "解壓程式跑在 DRAM",
                 [("dram", "kernel 解壓", "0x82000000 → 0x80008000")], None, None),
            ],
        },
    },
    "boot-memory-map": {
        "zh": {
            "title": "AM335x 開機時的完整記憶體地圖",
            "desc": "由高位址到低位址分成三個區域。DRAM（外部 DDR3）：U-Boot 本體、bootz 搬移後的 DTB 與 initrd、"
                    "load 放的 DTB 與 initrd、zImage、SPL 的 BSS、重定位前的 U-Boot、kernel 解壓位置。"
                    "中間是周邊暫存器，不是記憶體。晶片內 SRAM：MLO／SPL。晶片內 ROM：Boot ROM。"
                    "圓圈數字對應開機步驟。不按比例。",
            "rows": [
                ("region", "purple", "DRAM（外部 DDR3，512 MiB）", "DDR 要等 SPL 初始化後才能用"),
                ("addr", "0xA0000000", "DRAM 頂端"),
                ("0x9FF59000", "gray", "③ U-Boot 本體（重定位後）", "下方接 malloc、gd、stack"),
                ("0x8F5D2000", "teal", "④ DTB + initrd（bootz 搬過來）", "bootm_size 限制在 0x90000000 以下"),
                ("0x88000000", "purple", "④ DTB、initrd（fdtaddr / rdaddr）", None),
                ("0x82000000", "purple", "④ zImage（loadaddr）", None),
                ("0x80A00000", "gray", "② SPL 的 BSS 與 malloc", "DDR 一起來就移出 SRAM"),
                ("0x80800000", "purple", "② u-boot.img（重定位前）", None),
                ("0x80008000", "teal", "⑤ kernel 解壓到這裡", None),
                ("addr", "0x80000000", "DRAM 起點"),
                ("break", "周邊暫存器（MMIO，不是記憶體）：EMIF、UART0、GPIO1…"),
                ("region", "amber", "內部 SRAM（晶片內）", "上電就能用，Boot ROM 只能把東西放這裡"),
                ("0x402F0400", "amber", "① MLO / SPL", "ROM 的下載區到 0x4030B800，約 109 KB"),
                ("region", "gray", "Boot ROM（晶片內，唯讀）", "上電後 CPU 從這裡開始執行"),
                ("0x40020000", "amber", "Boot ROM 程式", "出廠就燒死"),
            ],
            "legend": ("load / 搬進來的位置", "之後被搬去的位置", "U-Boot 自己用的"),
        },
    },
}


def boot_chain(t, mode):
    stages = t["stages"]
    h = 40 + len(stages) * 86 - 30 + 60
    s = Svg(h, t["title"], t["desc"], mode)
    for i, (name, sub, ramp, note) in enumerate(stages):
        y = 40 + i * 86
        s.box(40, y, 280, 56, "purple", name, sub)
        s.leader(320, y + 28, 378, y + 28)
        s.box(380, y + 6, 260, 44, ramp, note, title_size=12)
        if i:
            s.arrow(180, y - 28, 180, y - 2)
    ly = 40 + len(stages) * 86 - 30 + 24
    s.swatch(40, ly, "amber", t["legend"][0])
    s.swatch(250, ly, "gray", t["legend"][1])
    return s.render()


def bootz_memory(t, mode):
    rows = t["rows"]
    y, layout = 44, []
    for addr, ramp, label, sub in rows:
        h = 56 if sub else 44
        layout.append((y, h, addr, ramp, label, sub))
        y += h + 10
    s = Svg(y + 34, t["title"], t["desc"], mode)
    s.text(184, 26, "0xA0000000", anchor="end")
    s.text(200, 26, t["top"])
    for y0, h, addr, ramp, label, sub in layout:
        s.box(200, y0, 320, h, ramp, label, sub)
        s.text(184, y0 + h / 2, addr, anchor="end")
    s.swatch(200, y + 12, "purple", t["legend"][0])
    s.swatch(400, y + 12, "teal", t["legend"][1])
    return s.render()


def gpio_led(t, mode):
    s = Svg(250, t["title"], t["desc"], mode)
    xs = [40, 193, 346, 499]
    for i, (name, reg, ramp, val, meaning) in enumerate(t["steps"]):
        x = xs[i]
        s.box(x, 40, 140, 56, "purple", name, reg)
        s.leader(x + 70, 96, x + 70, 140)
        s.box(x, 140, 140, 56, ramp, val, meaning)
        if i:
            s.arrow(xs[i - 1] + 142, 68, x - 2, 68)
    s.text(W / 2, 226, t["note"], anchor="middle")
    return s.render()


LANES = {"sram": (150, 130), "dram": (288, 230), "sd": (526, 134)}  # x, width


def boot_memory_flow(t, mode):
    y, layout = 66, []
    for step in t["steps"]:
        h = 74 if any(not isinstance(c[2], str) for c in step[2]) else 56
        layout.append((y, h, step))
        y += h + 14
    s = Svg(y + 10, t["title"], t["desc"], mode)
    for lane, (x, w) in LANES.items():
        ramp, title, sub = t["lanes"][lane]
        s.region(x, 12, w, y - 16, ramp, title, sub)
    for y0, h, (name, where, cells, move, note) in layout:
        s._text(20, y0 + h / 2 - 9, name, s.p["gray"][2], 13, 500, "start")
        s.text(20, y0 + h / 2 + 10, where)
        for lane, title, sub in cells:
            x, w = LANES[lane]
            s.box(x + 8, y0, w - 16, h, t["lanes"][lane][0], title, sub, title_size=13)
        if move:
            src, dst = (LANES[k] for k in move)
            s.arrow(src[0] + 6, y0 + h / 2, dst[0] + dst[1] - 6, y0 + h / 2)
            if note:
                x, w = LANES["dram"]
                s.text(x + w / 2, y0 + h / 2 - 12, note, size=11, anchor="middle")
    return s.render()


def boot_memory_map(t, mode):
    heights = {"region": 40, "addr": 18, "break": 36}
    y, layout = 16, []
    for row in t["rows"]:
        h = heights.get(row[0]) or (56 if row[3] else 44)
        if row[0] == "region" and layout and layout[-1][2][0] != "break":
            y += 16  # keep neighbouring region frames apart
        layout.append((y, h, row))
        y += h + (4 if row[0] in heights else 10)
    s = Svg(y + 40, t["title"], t["desc"], mode)
    # region frames first so the boxes sit on top of them
    starts = [i for i, (_, _, r) in enumerate(layout) if r[0] == "region"]
    for n, i in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(layout)
        end = next((j for j in range(i + 1, end) if layout[j][2][0] == "break"), end)
        y_end = layout[end - 1][0] + layout[end - 1][1]
        _, ramp, title, sub = layout[i][2]
        s.region(20, layout[i][0], W - 40, y_end - layout[i][0] + 10, ramp, title, sub)
    for y0, h, row in layout:
        if row[0] == "region":
            continue
        if row[0] == "addr":
            s.text(184, y0 + h / 2, row[1], anchor="end")
            s.text(200, y0 + h / 2, row[2])
        elif row[0] == "break":
            s.text(W / 2, y0 + h / 2 + 4, row[1], anchor="middle")
        else:
            addr, ramp, label, sub = row
            s.box(200, y0, 420, h, ramp, label, sub)
            s.text(184, y0 + h / 2, addr, anchor="end")
    s.swatch(40, y + 18, "purple", t["legend"][0])
    s.swatch(250, y + 18, "teal", t["legend"][1])
    s.swatch(450, y + 18, "gray", t["legend"][2])
    return s.render()


BUILDERS = {"boot-chain": boot_chain, "bootz-memory": bootz_memory, "gpio-led": gpio_led,
            "boot-memory-flow": boot_memory_flow, "boot-memory-map": boot_memory_map}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, langs in TEXT.items():
        for lang, t in langs.items():
            for mode in PALETTE:
                path = OUT / f"{name}-{lang}-{mode}.svg"
                path.write_text(BUILDERS[name](t, mode), encoding="utf-8")
                print(path.relative_to(OUT.parent.parent.parent))


if __name__ == "__main__":
    main()
