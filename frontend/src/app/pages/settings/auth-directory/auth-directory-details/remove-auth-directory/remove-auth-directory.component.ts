import { Component, Inject } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Router } from '@angular/router';

import { WaitService } from '../../../../../core/components/wait/wait.service';
import { AuthenticationDirectoryService } from '../../auth-directory.service';

@Component({
  selector: 'vdi-remove-auth-directory',
  templateUrl: './remove-auth-directory.component.html'
})

export class RemoveAuthenticationDirectoryComponent  {

  constructor(
              private waitService: WaitService,
              private dialogRef: MatDialogRef<RemoveAuthenticationDirectoryComponent>,
              private router: Router,
              @Inject(MAT_DIALOG_DATA) public data,
              private service: AuthenticationDirectoryService) {}

  public send() {
    this.waitService.setWait(true);
    this.service.deleteAuthDir(this.data).subscribe((res) => {
      if (res) {
        setTimeout(() => {
          this.dialogRef.close();
          this.router.navigate(['pages/settings/auth-directory']);
          this.service.getAllAuthenticationDirectory().refetch();
          this.waitService.setWait(false);
        }, 1000);
      }
    });
  }
}
