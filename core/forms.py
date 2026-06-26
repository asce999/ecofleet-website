import re

from django import forms

from . import cof
import zipfile
import logging

logger = logging.getLogger('core')

def validate_xlsx_upload(f):
    if not f:
        return f
        
    max_size = 10 * 1024 * 1024 # 10 MB
    if f.size > max_size:
        logger.warning(f"Upload rejected: {f.name} exceeds 10MB.")
        raise forms.ValidationError("File too large. Maximum size is 10MB.")
        
    name = f.name.lower()
    
    # Check for multiple executable extensions (e.g., .xlsx.exe)
    parts = name.split('.')
    if len(parts) > 2 and parts[-1] in ('exe', 'sh', 'bat', 'cmd', 'js', 'vbs', 'php'):
        logger.warning(f"Upload rejected: {f.name} has dangerous trailing extension.")
        raise forms.ValidationError("Dangerous file extension detected.")
        
    if not name.endswith('.xlsx'):
        logger.warning(f"Upload rejected: {f.name} is not an .xlsx file.")
        raise forms.ValidationError("Please upload a valid .xlsx Excel workbook.")
        
    try:
        f.seek(0)
        if not zipfile.is_zipfile(f):
            logger.warning(f"Upload rejected: {f.name} is not a valid ZIP/XLSX archive.")
            raise forms.ValidationError("File is corrupted or not a valid Excel archive.")
        f.seek(0)
    except Exception as e:
        logger.warning(f"Upload rejected: {f.name} could not be read: {e}")
        raise forms.ValidationError("File is corrupted or cannot be read.")
    
    return f



class WorkbookUploadForm(forms.Form):
    workbook = forms.FileField(label="Tracking Workbook (.xlsx)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['workbook'].widget.attrs.setdefault('class', 'portal-file')

    def clean_workbook(self):
        return validate_xlsx_upload(self.cleaned_data.get('workbook'))


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


class PendencyForm(forms.Form):
    file_2w = forms.FileField(label="2W Master Report (.xlsx)")
    file_cv = forms.FileField(label="CV Master Report (.xlsx)")
    report_name = forms.CharField(
        label="Report Name",
        help_text="The generated file is saved with this name.")
    min_delay_days = forms.IntegerField(
        label="Delayed by (days or more)", min_value=1, required=False, initial=1)
    all_in_transit = forms.BooleanField(
        label="Include everything in transit (ignore the delay threshold)",
        required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            w = field.widget
            if isinstance(w, forms.CheckboxInput):
                w.attrs.setdefault('class', 'portal-check')
            elif isinstance(w, forms.ClearableFileInput):
                w.attrs.setdefault('class', 'portal-file')
            else:
                w.attrs.setdefault('class', 'portal-input')

    def _check_xlsx(self, f):
        return validate_xlsx_upload(f)

    def clean_file_2w(self):
        return self._check_xlsx(self.cleaned_data['file_2w'])

    def clean_file_cv(self):
        return self._check_xlsx(self.cleaned_data['file_cv'])

    def clean_report_name(self):
        raw = (self.cleaned_data['report_name'] or '').strip()
        safe = re.sub(r'[^\w\s\-.]', '', raw).strip()
        if not safe:
            raise forms.ValidationError("Enter a valid report name.")
        if safe.lower().endswith('.xlsx'):
            safe = safe[:-5].strip()
        return safe

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('all_in_transit') and not cleaned.get('min_delay_days'):
            cleaned['min_delay_days'] = 1
        return cleaned


class MorningForm(forms.Form):
    file_2w = forms.FileField(label="Yesterday's 2W Report (.xlsx)")
    file_cv = forms.FileField(label="Yesterday's CV Report (.xlsx)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'portal-file')

    def _check_xlsx(self, f):
        return validate_xlsx_upload(f)

    def clean_file_2w(self):
        return self._check_xlsx(self.cleaned_data['file_2w'])

    def clean_file_cv(self):
        return self._check_xlsx(self.cleaned_data['file_cv'])


class PrevMonthUpdateForm(forms.Form):
    file_2w = forms.FileField(label="Previous Month's 2W Report (.xlsx)")
    file_cv = forms.FileField(label="Previous Month's CV Report (.xlsx)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'portal-file')

    def _check_xlsx(self, f):
        return validate_xlsx_upload(f)

    def clean_file_2w(self):
        return self._check_xlsx(self.cleaned_data['file_2w'])

    def clean_file_cv(self):
        return self._check_xlsx(self.cleaned_data['file_cv'])


class BtplShipmentForm(forms.Form):
    row_num = forms.IntegerField(widget=forms.HiddenInput())
    lr_number = forms.CharField(label="LR NUMBER", required=False)
    pickup_date = forms.DateField(
        label="Pickup Request Date",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    name = forms.CharField(label="Consignee/Customer Name", required=False)
    address = forms.CharField(
        label="Address",
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
    )
    contact_person = forms.CharField(label="Contact Person", required=False)
    contact_number = forms.CharField(label="Contact Number", required=False)
    city = forms.CharField(label="City", required=False)
    state = forms.CharField(label="State", required=False)
    boxes = forms.IntegerField(label="No Of Boxes", required=False)
    weight_ef = forms.FloatField(label="Weight as per EcoFleet", required=False)
    weight_opt = forms.FloatField(label="Weight as per Optlog", required=False)
    status = forms.CharField(label="Status", required=False)
    delivered_on = forms.DateField(
        label="Delivered on",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    tat = forms.IntegerField(label="TAT", required=False)
    rate = forms.FloatField(label="Rate", required=False)
    amount = forms.FloatField(label="Amount (leave blank for auto-formula)", required=False)
    vendor = forms.CharField(label="Vendor", required=False)
    vendor_rate = forms.FloatField(label="Vendor Rate", required=False)
    vendor_payment = forms.FloatField(label="CNG Paid & Vendor Payment", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            w = field.widget
            if not isinstance(w, forms.HiddenInput):
                css = 'portal-select' if isinstance(w, forms.Select) else 'portal-input'
                w.attrs.setdefault('class', css)


class BtplWorkbookUploadForm(forms.Form):
    workbook = forms.FileField(label="BTPL Shipment Workbook (.xlsx)", required=False)
    active_sheet = forms.ChoiceField(label="Active Sheet Tab", required=False, choices=[])

    def __init__(self, *args, **kwargs):
        sheets = kwargs.pop('sheets', [])
        super().__init__(*args, **kwargs)
        self.fields['workbook'].widget.attrs.setdefault('class', 'portal-file')
        self.fields['active_sheet'].widget.attrs.setdefault('class', 'portal-select')
        if sheets:
            self.fields['active_sheet'].choices = [(s, s) for s in sheets]
        else:
            self.fields['active_sheet'].choices = [('JUN 26', 'JUN 26')]

    def clean_workbook(self):
        return validate_xlsx_upload(self.cleaned_data.get('workbook'))


from .models import SalaryConfig

class SalaryConfigForm(forms.ModelForm):
    class Meta:
        model = SalaryConfig
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'portal-input')


class AttendanceWorkbookUploadForm(forms.Form):
    workbook = forms.FileField(label="Attendance Workbook (.xlsx)", required=False)
    active_sheet = forms.ChoiceField(label="Active Sheet Tab", required=False, choices=[])

    def __init__(self, *args, **kwargs):
        sheets = kwargs.pop('sheets', [])
        super().__init__(*args, **kwargs)
        self.fields['workbook'].widget.attrs.setdefault('class', 'portal-file')
        self.fields['active_sheet'].widget.attrs.setdefault('class', 'portal-select')
        if sheets:
            self.fields['active_sheet'].choices = [(s, s) for s in sheets]
        else:
            self.fields['active_sheet'].choices = [('JUNE 2026', 'JUNE 2026')]

    def clean_workbook(self):
        return validate_xlsx_upload(self.cleaned_data.get('workbook'))


class FtlShipmentForm(forms.Form):
    row_num = forms.IntegerField(widget=forms.HiddenInput())
    booking_date = forms.DateField(
        label="Date of Booking",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    etd = forms.DateField(
        label="ETD",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    delivery_date = forms.DateField(
        label="Date of Delivery",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    consignor = forms.CharField(label="Consignor", required=False)
    origin = forms.CharField(label="From Location (Origin)", required=False)
    consignee = forms.CharField(label="Consignee", required=False)
    lr_number = forms.CharField(label="LR Number", required=False)
    destination = forms.CharField(label="To Location (Destination)", required=False)
    vehicle_number = forms.CharField(label="Vehicle Number", required=False)
    vendor = forms.CharField(label="Vendor", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            w = field.widget
            if not isinstance(w, forms.HiddenInput):
                css = 'portal-select' if isinstance(w, forms.Select) else 'portal-input'
                w.attrs.setdefault('class', css)


class FtlWorkbookUploadForm(forms.Form):
    workbook = forms.FileField(label="FTL Shipment Workbook (.xlsx)", required=False)
    active_sheet = forms.ChoiceField(label="Active Sheet Tab", required=False, choices=[])

    def __init__(self, *args, **kwargs):
        sheets = kwargs.pop('sheets', [])
        super().__init__(*args, **kwargs)
        self.fields['workbook'].widget.attrs.setdefault('class', 'portal-file')
        self.fields['active_sheet'].widget.attrs.setdefault('class', 'portal-select')
        if sheets:
            self.fields['active_sheet'].choices = [(s, s) for s in sheets]
        else:
            self.fields['active_sheet'].choices = [('Sheet1', 'Sheet1')]

    def clean_workbook(self):
        return validate_xlsx_upload(self.cleaned_data.get('workbook'))



