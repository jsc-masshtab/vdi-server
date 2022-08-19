import { Component, Inject } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatDialog, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { WaitService } from '@app/core/components/wait/wait.service';
import { VmDetailsPopupService } from '../vm-details-popup.service';

@Component({
  selector: 'vdi-add-vm-connection',
  templateUrl: './add-vm-connection.component.html',
  styleUrls: ['./add-vm-connection.component.scss']
})
export class AddVmConnectionComponent {

  public checkValid: boolean = true;
  public form: FormGroup;

  public connection_types = this.data.typePool === 'rds' ? ['RDP', 'NATIVE_RDP'] : ['RDP', 'NATIVE_RDP', 'SPICE', 'SPICE_DIRECT', 'LOUDPLAY'];

  constructor(
    @Inject(MAT_DIALOG_DATA) public data,
    private waitService: WaitService,
    private service: VmDetailsPopupService,
    public dialog: MatDialog,
    private dialogRef: MatDialogRef<AddVmConnectionComponent>,
    private fb: FormBuilder,
  ) {
    this.initForm();
  }

  private initForm(): void {
    this.form = this.fb.group({
      connection_type: ['RDP', Validators.required],
      address: '',
      port: 1,
      active: true
    });
  }

  public send() {
    this.checkValid = true;
    if (this.form.status === 'VALID') {
      this.waitService.setWait(true);
      this.service.addVmConnectionData(this.data.vm.id, this.form.value).subscribe((res) => {
        if (res) {
          this.service.getVm().refetch();
          this.waitService.setWait(false);
          this.dialogRef.close();
        }
      });
    }
  }
}
