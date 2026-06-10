from django import forms

from . import cof


class WorkbookUploadForm(forms.Form):
    workbook = forms.FileField(label="Tracking Workbook (.xlsx)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['workbook'].widget.attrs.setdefault('class', 'portal-file')

    def clean_workbook(self):
        f = self.cleaned_data['workbook']
        if not f.name.lower().endswith('.xlsx'):
            raise forms.ValidationError("Please upload the .xlsx tracking workbook.")
        return f


class CofForm(forms.Form):
    # Shipment
    lr_number       = forms.CharField(label="LR Number")
    invoice_date    = forms.CharField(label="Invoice Date", required=False,
                        widget=forms.DateInput(attrs={'type': 'date'}))
    invoice_numbers = forms.CharField(label="Invoice Number(s)")
    remark          = forms.ChoiceField(label="Remark",
                        choices=[(r, r) for r in cof.REMARK_OPTIONS], required=False)
    transporter     = forms.ChoiceField(label="Transporter",
                        choices=[(t, t) for t in cof.TRANSPORTER_OPTIONS], required=False)
    biz             = forms.ChoiceField(label="Biz",
                        choices=[(b, b) for b in cof.BIZ_OPTIONS], required=False)
    state           = forms.CharField(label="State", required=False)
    # Dealer
    dealer_code     = forms.CharField(label="Dealer Code", required=False)
    dealer_name     = forms.CharField(label="Dealer Name")
    # Invoice / package
    ndp_price       = forms.DecimalField(label="NDP Price (Rs)", min_value=0,
                        max_digits=12, decimal_places=2)
    disc_qty        = forms.DecimalField(label="Discrepancy Qty", min_value=0,
                        max_digits=12, decimal_places=2)
    weight          = forms.CharField(label="Weight (kg)", required=False)
    num_packages    = forms.CharField(label="No. of Packages", required=False)
    pickup_date     = forms.CharField(label="Pickup Date (LR Date)", required=False,
                        widget=forms.DateInput(attrs={'type': 'date'}))
    delivery_date   = forms.CharField(label="Delivery Date", required=False,
                        widget=forms.DateInput(attrs={'type': 'date'}))
    # Consignee
    consignee_name    = forms.CharField(label="Consignee Name")
    destination_city  = forms.CharField(label="Destination City", required=False)
    consignee_address = forms.CharField(label="Consignee Address", required=False)
    consignee_state   = forms.CharField(label="Consignee State", required=False)
    # Status
    status_delhivery = forms.CharField(label="Status with Delhivery",
                        required=False, initial="Not Sent")
    ref_delhivery    = forms.CharField(label="Reference for Delhivery",
                        required=False, initial="Not Sent")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = 'portal-select' if isinstance(field.widget, forms.Select) else 'portal-input'
            field.widget.attrs.setdefault('class', css)

    def clean(self):
        cleaned = super().clean()
        for field, label in [("invoice_date", "Invoice Date"),
                             ("pickup_date", "Pickup Date"),
                             ("delivery_date", "Delivery Date")]:
            v = cleaned.get(field)
            if v and cof.parse_date(v) is None:
                self.add_error(field, "Invalid date — use DD/MM/YYYY.")
        ndp = cleaned.get("ndp_price") or 0
        qty = cleaned.get("disc_qty") or 0
        if (ndp * qty) == 0:
            raise forms.ValidationError(
                "Loss Amount must be greater than 0 (NDP Price × Discrepancy Qty).")
        return cleaned

    def to_cof_data(self):
        c = self.cleaned_data
        loss = float(c["ndp_price"]) * float(c["disc_qty"])
        g = lambda k: (c.get(k) or "").strip()
        return {
            "lr_number": g("lr_number"),
            "invoice_date": g("invoice_date"),
            "invoice_numbers": g("invoice_numbers"),
            "remark": g("remark"),
            "transporter": g("transporter"),
            "biz": g("biz"),
            "state": g("state"),
            "dealer_code": g("dealer_code"),
            "dealer_name": g("dealer_name"),
            "loss_amount": round(loss, 2),
            "weight": g("weight"),
            "num_packages": g("num_packages"),
            "pickup_date": g("pickup_date"),
            "delivery_date": g("delivery_date"),
            "consignee_name": g("consignee_name"),
            "consignee_address": g("consignee_address"),
            "consignee_state": g("consignee_state"),
            "destination_city": g("destination_city"),
            "status_delhivery": g("status_delhivery") or "Not Sent",
            "ref_delhivery": g("ref_delhivery") or "Not Sent",
        }
