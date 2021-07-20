import { UsersService } from '../../users.service';

import { WaitService } from '../../../../../common/components/single/wait/wait.service';
import { MatDialogRef } from '@angular/material/dialog';
import { Component, Inject, OnDestroy } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'vdi-add-group',
  templateUrl: './add-group.component.html'
})

export class AddGropComponent implements OnDestroy {

  public pending: boolean = false;
  public groups: [] = [];
  private destroy: Subject<any> = new Subject<any>();
  public valid: boolean = true;

  constructor(private service: UsersService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<AddGropComponent>,
              @Inject(MAT_DIALOG_DATA) public data: any) { }

  public send() {
    if (this.groups.length) {
      this.waitService.setWait(true);
      this.service
        .addGrop(this.data.id, this.groups)
        .pipe(takeUntil(this.destroy)).subscribe((res) => {
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
