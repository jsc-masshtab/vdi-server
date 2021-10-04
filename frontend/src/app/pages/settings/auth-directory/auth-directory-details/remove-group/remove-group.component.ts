import { Component, Inject, OnDestroy } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { WaitService } from '../../../../../core/components/wait/wait.service';
import { AuthenticationDirectoryService } from '../../auth-directory.service';

@Component({
  selector: 'vdi-remove-user',
  templateUrl: './remove-group.component.html'
})

export class RemoveGroupComponent implements OnDestroy {

  public pending: boolean = false;
  public group: string;
  private destroy: Subject<any> = new Subject<any>();
  public valid: boolean = true;

  constructor(private service: AuthenticationDirectoryService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<RemoveGroupComponent>,
              @Inject(MAT_DIALOG_DATA) public data: any) { }



  public send() {
    if (this.group) {
      this.waitService.setWait(true);
      this.service.removeGroup(this.group).pipe(takeUntil(this.destroy)).subscribe((res) => {
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

  public select(select) {
    this.group = select['value'];
    this.valid = true;
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }

}
