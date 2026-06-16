from django.shortcuts import render, redirect
from django.contrib import messages
from core.models import ToolRun
from core.forms import PrevMonthUpdateForm
from core.decorators import staff_required, tool_permission_required
from core import prev_month as prev_month_logic


@staff_required
@tool_permission_required('prev_month')
def prev_month_update(request):
    if request.method == 'POST':
        form = PrevMonthUpdateForm(request.POST, request.FILES)
        delhivery_files = request.FILES.getlist('delhivery_files')
        ok = form.is_valid()
        if not delhivery_files:
            messages.error(request, "Upload at least one Delhivery CSV.")
            ok = False
        elif any(not f.name.lower().endswith('.csv') for f in delhivery_files):
            messages.error(request, "Delhivery files must be .csv.")
            ok = False

        if ok:
            try:
                result = prev_month_logic.generate(
                    delhivery_files, form.cleaned_data['file_2w'], form.cleaned_data['file_cv'])
            except prev_month_logic.ReportError as e:
                messages.error(request, str(e))
            except Exception as e:
                ToolRun.objects.create(
                    user=request.user, tool=ToolRun.TOOL_PREV_MONTH,
                    status=ToolRun.STATUS_FAILED, detail=f"Error: {e}")
                messages.error(request, f"Failed to run previous month update: {e}")
            else:
                s = result['summary']
                run = ToolRun.objects.create(
                    user=request.user, tool=ToolRun.TOOL_PREV_MONTH,
                    status=ToolRun.STATUS_SUCCESS,
                    reference=f"Previous Month Update {datetime.date.today():%d %b %Y}",
                    detail=(f"2W: {s['two_w']['updated']} updated ({s['two_w']['delivered']} delivered / {s['two_w']['in_transit']} in transit) · "
                            f"CV: {s['cv']['updated']} updated ({s['cv']['delivered']} delivered / {s['cv']['in_transit']} in transit) · "
                            f"{s['delhivery_rows']} Delhivery rows"))
                for key in ("2W", "CV"):
                    buf, fname = result[key]
                    ToolRunFile.objects.create(
                        run=run, label=f"{key} master", download_name=fname,
                        file=ContentFile(buf.getvalue(), name=fname))
                messages.success(request, "Previous month update completed.")
                return redirect('tool_result', pk=run.pk)
    else:
        form = PrevMonthUpdateForm()
    return render(request, 'core/portal/prev_month_form.html',
                  {'active': 'prev_month', 'form': form})


