import { WaitService } from '../../../common/components/single/wait/wait.service';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material';
import { Component, Inject } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { EventsService } from '../all-events/events.service';
import { LogSettingService } from '../../log-setting/log-setting.service';


@Component({
  selector: 'vdi-add-exports',
  templateUrl: './add-exports.component.html'
})

export class AddExportComponent {

  public form: FormGroup;
  public checkValid: boolean = false;
  public dir_path: string;

  private initForm(): void {
    this.settings.getSettings().valueChanges.pipe().subscribe((res) => {
      this.dir_path = res.data.journal_settings.dir_path;
    });
    this.form = this.fb.group({
      start: ['', Validators.required],
      finish: ['', Validators.required],
      path: ['', Validators.required]
    });
  }

  constructor(
    private service: EventsService,
    private settings: LogSettingService,
    private dialogRef: MatDialogRef<AddExportComponent>,
    private fb: FormBuilder,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private waitService: WaitService) {
    this.initForm();
  }

  public send() {
    this.checkValid = true;

    if (this.form.status === 'VALID') {

      this.waitService.setWait(true);

      this.service.createExport({ ...this.form.value }).subscribe(() => {
        this.service.getAllEvents(this.data.queryset).refetch();
        this.dialogRef.close();
        this.waitService.setWait(false);
      });
    }
  }
}
