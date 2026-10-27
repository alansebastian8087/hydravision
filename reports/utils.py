import io
import qrcode
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
)

from payments.models import Payment
from samples.models import TestResult


def generate_qr_code(report, qr_text):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=8,
        border=4,
    )
    qr.add_data(qr_text)
    qr.make(fit=True)

    qr_image = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    qr_image.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer


def get_parameter_rows(test_result):
    if not test_result:
        return []

    return [
        {
            "name": "pH",
            "value": test_result.ph,
            "unit": "",
            "reference": "6.5 - 8.5",
            "safe": 6.5 <= test_result.ph <= 8.5,
            "chart_value": abs(test_result.ph - 7.5) / 1.0,
        },
        {
            "name": "TDS",
            "value": test_result.tds,
            "unit": "mg/L",
            "reference": "≤ 500 mg/L",
            "safe": test_result.tds <= 500,
            "chart_value": test_result.tds / 500,
        },
        {
            "name": "Turbidity",
            "value": test_result.turbidity,
            "unit": "NTU",
            "reference": "≤ 1 NTU",
            "safe": test_result.turbidity <= 1,
            "chart_value": test_result.turbidity / 1,
        },
        {
            "name": "Hardness",
            "value": test_result.hardness,
            "unit": "mg/L",
            "reference": "≤ 200 mg/L",
            "safe": test_result.hardness <= 200,
            "chart_value": test_result.hardness / 200,
        },
        {
            "name": "Fluoride",
            "value": test_result.fluoride,
            "unit": "mg/L",
            "reference": "≤ 1.0 mg/L",
            "safe": test_result.fluoride <= 1.0,
            "chart_value": test_result.fluoride / 1.0,
        },
        {
            "name": "Iron",
            "value": test_result.iron,
            "unit": "mg/L",
            "reference": "≤ 0.3 mg/L",
            "safe": test_result.iron <= 0.3,
            "chart_value": test_result.iron / 0.3,
        },
        {
            "name": "Nitrate",
            "value": test_result.nitrate,
            "unit": "mg/L",
            "reference": "≤ 45 mg/L",
            "safe": test_result.nitrate <= 45,
            "chart_value": test_result.nitrate / 45,
        },
        {
            "name": "Chloride",
            "value": test_result.chloride,
            "unit": "mg/L",
            "reference": "≤ 250 mg/L",
            "safe": test_result.chloride <= 250,
            "chart_value": test_result.chloride / 250,
        },
        {
            "name": "Sulphate",
            "value": test_result.sulphate,
            "unit": "mg/L",
            "reference": "≤ 200 mg/L",
            "safe": test_result.sulphate <= 200,
            "chart_value": test_result.sulphate / 200,
        },
        {
            "name": "Alkalinity",
            "value": test_result.alkalinity,
            "unit": "mg/L as CaCO₃",
            "reference": "≤ 200 mg/L",
            "safe": test_result.alkalinity <= 200,
            "chart_value": test_result.alkalinity / 200,
        },
    ]


def build_customer_chart_image(test_result):
    parameter_rows = get_parameter_rows(test_result)

    labels = [row["name"] for row in parameter_rows]
    normalized_values = [min(row["chart_value"], 1.35) for row in parameter_rows]
    bar_colors = [
        "#22a06b" if row["safe"] else "#d64545"
        for row in parameter_rows
    ]

    fig, ax = plt.subplots(figsize=(8.1, 4.4))
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#fbfdfe")

    bars = ax.barh(
        labels,
        normalized_values,
        color=bar_colors,
        edgecolor="#ffffff",
        height=0.62,
    )

    ax.axvspan(0, 1, color="#dff4e8", alpha=0.75, zorder=0)
    ax.axvline(
        1,
        color="#d64545",
        linewidth=1.4,
        linestyle="--",
        label="Acceptable limit"
    )

    ax.set_xlim(0, 1.35)
    ax.set_xlabel(
        "Measured result compared with its acceptable limit",
        fontsize=9
    )
    ax.set_title(
        "Customer-Friendly Water Quality Summary",
        fontsize=12,
        fontweight="bold",
        pad=12
    )

    ax.set_xticks([0, 0.5, 1, 1.25])
    ax.set_xticklabels(
        ["Low", "Half limit", "Limit", "Above limit"],
        fontsize=8
    )

    ax.tick_params(axis="y", labelsize=8)
    ax.grid(axis="x", linestyle="--", alpha=0.22)
    ax.invert_yaxis()

    for bar, row in zip(bars, parameter_rows):
        result_label = f"{row['value']} {row['unit']}".strip()
        status_label = "SAFE" if row["safe"] else "ATTENTION"

        label_x = min(bar.get_width() + 0.02, 1.28)

        ax.text(
            label_x,
            bar.get_y() + bar.get_height() / 2,
            f"{result_label}  •  {status_label}",
            va="center",
            ha="left",
            fontsize=7.5,
            color="#1c2e3a",
        )

    ax.legend(
        loc="lower right",
        fontsize=8,
        frameon=False
    )

    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.tight_layout()

    image_buffer = io.BytesIO()
    fig.savefig(
        image_buffer,
        format="PNG",
        dpi=180,
        bbox_inches="tight",
        facecolor=fig.get_facecolor()
    )
    plt.close(fig)

    image_buffer.seek(0)
    return image_buffer


def get_status_label(is_safe):
    return "Safe" if is_safe else "Needs Attention"


def get_status_color(is_safe):
    if is_safe:
        return colors.HexColor("#eaf8f1")

    return colors.HexColor("#fff1f4")


def get_status_text_color(is_safe):
    if is_safe:
        return colors.HexColor("#157152")

    return colors.HexColor("#a12e4c")


def generate_pdf_report(report, request=None):
    sample = report.water_test.sample
    water_test = report.water_test
    test_result = TestResult.objects.filter(water_test=water_test).first()
    payment = Payment.objects.filter(sample=sample).order_by("-id").first()

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0c4f66"),
        alignment=TA_CENTER,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#526d7a"),
        alignment=TA_CENTER,
        spaceAfter=10,
    )

    heading_style = ParagraphStyle(
        "HeadingStyle",
        parent=styles["Heading2"],
        fontSize=11.5,
        leading=14,
        textColor=colors.HexColor("#0f3638"),
        alignment=TA_LEFT,
        spaceBefore=7,
        spaceAfter=7,
    )

    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["BodyText"],
        fontSize=9.3,
        leading=13,
        textColor=colors.HexColor("#233645"),
        alignment=TA_LEFT,
        spaceBefore=0,
        spaceAfter=3,
    )

    safe_style = ParagraphStyle(
        "SafeStyle",
        parent=body_style,
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#157152"),
    )

    unsafe_style = ParagraphStyle(
        "UnsafeStyle",
        parent=body_style,
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#a12e4c"),
    )

    qr_caption_style = ParagraphStyle(
        "QrCaptionStyle",
        parent=body_style,
        fontSize=8.5,
        leading=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#526d7a"),
    )

    elements = []

    elements.append(
        Paragraph("HydraVision Water Quality Report", title_style)
    )
    elements.append(
        Paragraph(
            "Laboratory result summary for customer-friendly understanding of the tested water sample.",
            subtitle_style
        )
    )

    meta_data = [
        ["Sample Code", sample.sample_code],
        ["Customer Name", sample.customer.name],
        ["Water Source", sample.water_source],
        ["Collection Date", str(sample.collection_date or "-")],
        ["Test Date", str(water_test.test_date or "-")],
        ["Payment Status", payment.payment_status if payment else "No Payment Record"],
        ["Water Quality Score", f"{water_test.water_quality_score or 0} / 100"],
        ["Final Status", water_test.bis_status or "Pending"],
    ]

    meta_table = Table(
        meta_data,
        colWidths=[135, 350],
        hAlign="LEFT",
    )

    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e7f6fd")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1c2e3a")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c8dbe5")),
        ("FONTSIZE", (0, 0), (-1, -1), 9.3),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    elements.append(meta_table)
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Final Result", heading_style))

    if water_test.bis_status == "Safe":
        elements.append(
            Paragraph(
                "Safe water sample — all tested values are within the configured acceptable limits.",
                safe_style
            )
        )
    else:
        elements.append(
            Paragraph(
                "Water needs treatment — one or more tested values are outside the configured acceptable limits.",
                unsafe_style
            )
        )

    elements.append(
        Paragraph(
            f"<b>Recommendation:</b> {water_test.recommendation or 'No recommendation available.'}",
            body_style
        )
    )
    elements.append(Spacer(1, 8))

    if test_result:
        parameter_rows = get_parameter_rows(test_result)

        elements.append(Paragraph("Parameter Results", heading_style))

        param_data = [[
            "Parameter",
            "Measured Value",
            "BIS Reference",
            "Status",
        ]]

        for row in parameter_rows:
            measured_value = f"{row['value']} {row['unit']}".strip()

            param_data.append([
                Paragraph(row["name"], body_style),
                Paragraph(measured_value, body_style),
                Paragraph(row["reference"], body_style),
                Paragraph(
                    get_status_label(row["safe"]),
                    body_style
                ),
            ])

        param_table = Table(
            param_data,
            colWidths=[105, 130, 145, 85],
            hAlign="LEFT",
        )

        table_style_commands = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1489c9")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#d0e0e8")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                colors.white,
                colors.HexColor("#f6fbfe")
            ]),
            ("FONTSIZE", (0, 0), (-1, -1), 8.7),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]

        for row_number, row in enumerate(parameter_rows, start=1):
            table_style_commands.append((
                "BACKGROUND",
                (3, row_number),
                (3, row_number),
                get_status_color(row["safe"])
            ))

            table_style_commands.append((
                "TEXTCOLOR",
                (3, row_number),
                (3, row_number),
                get_status_text_color(row["safe"])
            ))

        param_table.setStyle(TableStyle(table_style_commands))

        elements.append(param_table)
        elements.append(Spacer(1, 10))

        elements.append(
            Paragraph(
                "Water Quality Summary Graph",
                heading_style
            )
        )

        elements.append(
            Paragraph(
                "Each bar compares a result with its own acceptable limit. Green indicates a value within the limit; red indicates a value requiring attention.",
                body_style
            )
        )

        chart_buffer = build_customer_chart_image(test_result)
        chart_image = Image(
            chart_buffer,
            width=165 * mm,
            height=88 * mm
        )
        chart_image.hAlign = "LEFT"

        elements.append(chart_image)
        elements.append(Spacer(1, 10))

    elements.append(Paragraph("QR Verification", heading_style))

    if report.qr_code:
        try:
            qr_image = Image(
                report.qr_code.path,
                width=34 * mm,
                height=34 * mm
            )

            qr_table = Table(
                [[
                    qr_image,
                    Paragraph(
                        "<b>Scan to verify this HydraVision report.</b><br/>"
                        "The QR code opens this report in the HydraVision system. "
                        "Use it to confirm the sample report details and final water-quality status.",
                        body_style
                    )
                ]],
                colWidths=[45 * mm, 120 * mm],
                hAlign="LEFT",
            )

            qr_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f4fbfe")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#c8dbe5")),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]))

            elements.append(qr_table)

        except Exception:
            elements.append(
                Paragraph(
                    "QR verification image could not be embedded in this PDF.",
                    body_style
                )
            )
    else:
        elements.append(
            Paragraph(
                "QR code is not available for this report.",
                body_style
            )
        )

    elements.append(Spacer(1, 12))
    elements.append(
        Paragraph(
            "HydraVision • Accurate testing • Reliable reports • Safer water decisions",
            qr_caption_style
        )
    )

    doc.build(elements)

    buffer.seek(0)
    return buffer