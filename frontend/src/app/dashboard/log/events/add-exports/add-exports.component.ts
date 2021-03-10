import { WaitService } from '../../../common/components/single/wait/wait.service';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material';
import { Component, Inject } from '@angular/core';
import { FormBuilder, FormGroup, Validators, FormControl } from '@angular/forms';
import { EventsService } from '../all-events/events.service';
import { LogSettingService } from '../../log-setting/log-setting.service';


@Component({
  selector: 'vdi-add-exports',
  templateUrl: './add-exports.component.html'
})

export class AddExportComponent {

  public init = false;
  public form: FormGroup;
  public checkValid: boolean = false;
  public dir_path: string;

  private initForm(): void {
    this.settings.getSettings().valueChanges.pipe().subscribe((res) => {
      this.dir_path = res.data.journal_settings.dir_path;
      this.form = this.fb.group({
        start: new FormControl(new Date(), Validators.required),
        finish: new FormControl(new Date(), Validators.required),
        journal_path: [this.dir_path, Validators.required]
      });

      this.init = true;
    });
  }

  constructor(
    private service: EventsService,
    private settings: LogSettingService,
    private dialogRef: MatDialogRef<AddExportComponent>,
    private fb: FormBuilder,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private waitService: WaitService) { }

  ngOnInit() {
    this.initForm();
  }

  public send() {
    this.checkValid = true;

    if (this.form.status === 'VALID') {

      this.waitService.setWait(true);

      const form = this.form.value;
      const start_date = new Date(form.start).setHours(0, 0, 0);
      const finish_date = new Date(form.finish).setHours(23, 59, 59);

      const data = {
        ...form,
        start: new Date(start_date).toISOString(),
        finish: new Date(finish_date).toISOString()
      };

      this.service.createExport(data).subscribe(() => {
        this.service.getAllEvents(this.data.queryset).refetch();
        this.dialogRef.close();
        this.waitService.setWait(false);
      });
    }
  }
}
