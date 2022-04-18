import { Component, Inject, OnInit } from '@angular/core';
import { MatDialog, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { FormControl } from '@angular/forms';
import { WaitService } from '@core/components/wait/wait.service';
import { VmDetailsPopupService } from '../vm-details-popup.service';

@Component({
  selector: 'vdi-remove-user-vm',
  templateUrl: './remove-user.component.html'
})

export class RemoveUserVmComponent implements OnInit {

  public users = new FormControl([]);
  public valid: boolean = true;

  public usersList: any[] = []

  constructor(
    private waitService: WaitService,
    private service: VmDetailsPopupService,
    public dialog: MatDialog,
    @Inject(MAT_DIALOG_DATA) public data,
  ) {}

  ngOnInit() {
    const assignedList = this.data.vm.assigned_users || [];
    this.usersList = [ ...assignedList ];
  }

  public send() {

    const users = this.users.value;

    if (users.length) {
      this.waitService.setWait(true);
      this.service.freeVmFromUser(this.data.vm.id, users).subscribe((res) => {
        if (res) {
          this.service.getVm().refetch()
          this.waitService.setWait(false);
          this.dialog.closeAll();
        }
      });
    } else {
      this.valid = false;
    }
  }
}
