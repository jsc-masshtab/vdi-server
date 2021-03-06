
import { Component, Inject, OnDestroy } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { WaitService } from '../../../../../core/components/wait/wait.service';
import { UsersService } from '../../users.service';

@Component({
  selector: 'vdi-remove-user',
  templateUrl: './remove-group.component.html'
})

export class RemoveGroupComponent implements OnDestroy {

  public pending: boolean = false;
  public groups: [] = [];
  private destroy: Subject<any> = new Subject<any>();
  public valid: boolean = true;

  constructor(private service: UsersService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<RemoveGroupComponent>,
              @Inject(MAT_DIALOG_DATA) public data: any) { }



  public send() {
    if (this.groups.length) {
      this.waitService.setWait(true);
      this.service.removeGroup(this.data.id, this.groups).pipe(takeUntil(this.destroy)).subscribe((res) => {
        if (res) {
          this.service.getUser(this.data.id).refetch();
          this.waitService.setWait(false);
          this.dialogRef.close();
        }
      });
    } else {
      this.valid = false;
    }
  }

  public select(value: []) {
    this.groups = value['value'];
    this.valid = true;
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }

}
