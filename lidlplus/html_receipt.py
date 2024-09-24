from typing import Any
import re

import lxml.html as html


VAT_TYPE_LINE_ENDING_PATTERN = re.compile(r" [A-Z]$")


def parse_html_receipt(date: str, html_receipt: str) -> dict[str, Any]:
    dom = html.document_fromstring(html_receipt)

    receipt = {
        "date": date,
        "itemsLine": [],
    }
    for node in dom.xpath(r".//span[starts-with(@id, 'purchase_list_line_')]"):
        if "class" not in node.attrib:
            if not VAT_TYPE_LINE_ENDING_PATTERN.search(node.text):
                continue

            *name_parts, price = node.text[:-2].split()
            receipt["itemsLine"].append(
                {
                    "name": " ".join(name_parts),
                    "originalAmount": price,
                    "isWeight": True,
                    "discounts": [],
                }
            )
        elif node.attrib["class"] == "currency":
            receipt["currency"] = {"code": node.text.strip(), "symbol": node.attrib["data-currency"]}
        elif node.attrib["class"] == "article":
            if node.text.startswith(" "):
                continue

            quantity_text = node.get("data-art-quantity")
            if quantity_text is None:
                is_weight = False
                quantity = 1
            elif "," in quantity_text:
                is_weight = True
                quantity = quantity_text
            else:
                is_weight = False
                quantity = quantity_text

            receipt["itemsLine"].append(
                {
                    "name": node.attrib["data-art-description"],
                    "currentUnitPrice": node.attrib["data-unit-price"],
                    "isWeight": is_weight,
                    "quantity": quantity,
                    "discounts": [],
                }
            )
        elif node.attrib["class"] == "discount":
            discount = abs(parse_float(node.text.split()[-1]))
            receipt["itemsLine"][-1]["discounts"].append({"amount": str(discount).replace(".", ",")})

    return receipt


def parse_float(text: str) -> float:
    return float(text.replace(",", "."))
