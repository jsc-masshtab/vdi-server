import { WaitService } from '../../../../common/components/single/wait/wait.service';
import { MatDialogRef } from '@angular/material';
import { Component, Inject, OnDestroy } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { AuthenticationDirectoryService } from '../../auth-directory.service';

@Component({
  selector: 'vdi-sync-group',
  templateUrl: './sync-group.component.html'
})

export class SyncGropComponent implements OnDestroy {

  public pending: boolean = false;
  public group: any = {};
  private destroy: Subject<any> = new Subject<any>();
  public valid: boolean = true;

  constructor(private service: AuthenticationDirectoryService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<SyncGropComponent>,
              @Inject(MAT_DIALOG_DATA) public data: any) { }

  public send() {
    if (this.group) {

      const data = {
        group_id: this.group,
        auth_dir_id: this.data.id
      }

      this.waitService.setWait(true);
      this.service
        .syncExistAuthDirGroupUsers(data)
        .pipe(takeUntil(this.destroy)).subscribe((res) => {
          if (res) {
            this.service.getAuthenticationDirectory(this.data.id).refetch();
            this.waitService.setWait(false);
            this.dialogRef.close();
          }
        });
    } else {
      this.valid = false;
    }
  }

  public select(type, select) {
    if (type == 'groups') {

      this.group = select.value['id'];
      this.valid = true;
    }
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }

}
