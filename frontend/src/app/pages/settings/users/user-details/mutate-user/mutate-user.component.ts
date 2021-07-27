import { Component, Inject } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';

import { WaitService } from '../../../../../core/components/wait/wait.service';
import { UsersService } from '../../users.service';

@Component({
  selector: 'mutate-user',
  templateUrl: './mutate-user.component.html',
  styleUrls: ['./mutate-user.component.scss']
})
export class MutateUserComponent {

  constructor(
    private waitService: WaitService,
    private dialogRef: MatDialogRef<MutateUserComponent>,
    @Inject(MAT_DIALOG_DATA) public data,
    private service: UsersService) { }

  public send() {
    this.waitService.setWait(true);
    this.service.mutate(this.data.params).subscribe((res) => {
      if (res) {
        setTimeout(() => {
          this.dialogRef.close();
          this.service.getUser(this.data.id).refetch();
          this.service.getAllUsers().refetch();
          this.waitService.setWait(false);
        }, 1000);
      }
    });
  }
}
