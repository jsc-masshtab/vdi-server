import { Component, Inject } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Router } from '@angular/router';
import { WaitService } from '@app/core/components/wait/wait.service';
import { UsersService } from '../../users.service';


interface IData {
  id: number;
  username: string;
}

@Component({
  selector: 'vdi-delete-user',
  templateUrl: './remove-user.component.html'
})

export class DeleteUserComponent  {

  constructor(
    private service: UsersService,
    private waitService: WaitService,
    private dialogRef: MatDialogRef<DeleteUserComponent>,
    private router: Router,
    @Inject(MAT_DIALOG_DATA) public data: IData
  ) {}

  public send() {
    this.waitService.setWait(true);
    this.service.deleteUser(this.data).subscribe(() => {
      this.dialogRef.close();
      this.router.navigate(['pages/settings/users']);
      this.waitService.setWait(false);
      this.service.portal.next('reload');
    });
  }
}
