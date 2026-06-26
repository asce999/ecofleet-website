# UAT (User Acceptance Testing) Checklist

## Functional Validations
- [ ] Employee Portal Login works with Active Directory / configured users.
- [ ] Password resets function as expected.
- [ ] User role permissions block unauthorized access (e.g. standard employees cannot view "User Permissions").
- [ ] File Uploads (Attendance, BTPL) correctly validate MIME types and reject corrupted files.
- [ ] File Uploads block executable files from being uploaded.
- [ ] Salary generation correctly calculates days worked, deductions, and DA.
- [ ] COF generation builds `.docx` files accurately.

## Operations validations
- [ ] Operations Center loads within 1 second.
- [ ] Operations Center accurately reflects the latest backup date.
- [ ] Intentionally deleting the COF letterhead correctly triggers a "Critical" alert on the Operations Center.
- [ ] Manual database backup completes successfully via CLI.

## Non-Functional
- [ ] Responsive design functions correctly on mobile tablets used by staff.
- [ ] UI maintains theme consistency (dark/light mode).
