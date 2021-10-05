import { Component, Inject, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialog } from '@angular/material/dialog';
import { FormControl } from '@angular/forms';

import { WaitService } from '../../../../../core/components/wait/wait.service';
import { PoolDetailsService } from '../../pool-details.service';

@Component({
  selector: 'vdi-add-user-vm',
  templateUrl: './add-user.component.html'
})

export class AddUserVmComponent implements OnInit {

  public users = new FormControl([]);
  public valid: boolean = true;

  public usersList: any[] = []

  constructor(
    private waitService: WaitService,
    private poolService: PoolDetailsService,
    @Inject(MAT_DIALOG_DATA) public data,
    public dialog: MatDialog
  ) {}

  ngOnInit() {
    const userList = this.data.usersPool || [];
    const assignedList = this.data.vm.assigned_users || [];

    this.usersList = userList.filter(user => !assignedList.some(assigned_users => assigned_users.id === user.id))
  }

  public send() {
    
    const users = this.users.value;

    if (users.length) {
      this.waitService.setWait(true);
      this.poolService.assignVmToUser(this.data.vm.id, users).subscribe((res) => {
        if (res) {
          this.poolService.getPool(this.data.idPool, this.data.typePool).refetch()
          this.waitService.setWait(false);
          this.dialog.closeAll();
        }
      });
    } else {
      this.valid = false;
    }
  }
}
