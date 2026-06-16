from django.shortcuts import render, redirect
from django.contrib import messages
from core.models import ToolRun
from core.forms import MorningForm
from core.decorators import staff_required, tool_permission_required
from core import morning as morning_logic


@staff_required
@tool_permission_required('morning')
def morning_report(request):
    if request.method == 'POST':
        form = MorningForm(request.POST, request.FILES)
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
                result = morning_logic.generate(
                    delhivery_files, form.cleaned_data['file_2w'], form.cleaned_data['file_cv'])
            except morning_logic.ReportError as e:
                messages.error(request, str(e))
            except Exception as e:
                ToolRun.objects.create(
                    user=request.user, tool=ToolRun.TOOL_MORNING,
                    status=ToolRun.STATUS_FAILED, detail=f"Error: {e}")
                messages.error(request, f"Failed to generate report: {e}")
            else:
                s = result['summary']
                run = ToolRun.objects.create(
                    user=request.user, tool=ToolRun.TOOL_MORNING,
                    status=ToolRun.STATUS_SUCCESS,
                    reference=f"Morning Report {datetime.date.today():%d %b %Y}",
                    detail=(f"2W: {s['two_w']['updated']} updated / {s['two_w']['new']} new · "
                            f"CV: {s['cv']['updated']} updated / {s['cv']['new']} new · "
                            f"{s['delhivery_rows']} Delhivery rows"))
                for key in ("2W", "CV"):
                    buf, fname = result[key]
                    ToolRunFile.objects.create(
                        run=run, label=f"{key} master", download_name=fname,
                        file=ContentFile(buf.getvalue(), name=fname))
                messages.success(request, "Morning report generated.")
                return redirect('tool_result', pk=run.pk)
        # fall through to re-render with errors
    else:
        form = MorningForm()
    return render(request, 'core/portal/morning_form.html',
                  {'active': 'morning', 'form': form})


