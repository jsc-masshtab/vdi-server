import { PoolDetailsService } from '../pool-details.service';

import { MatDialogRef } from '@angular/material';
import { Component, Inject, OnDestroy } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { WaitService } from 'src/app/dashboard/common/components/single/wait/wait.service';
import { PoolsUpdateService } from '../../all-pools/pools.update.service';

@Component({
  selector: 'vdi-add-group',
  templateUrl: './add-group.component.html'
})

export class AddGropComponent implements OnDestroy {

  public pending: boolean = false;
  public groups: [] = [];
  private destroy: Subject<any> = new Subject<any>();
  public valid: boolean = true;

  constructor(private service: PoolDetailsService,
              private updatePools: PoolsUpdateService,
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
            this.service.getPool(this.data.idPool, this.data.typePool).refetch();
            this.updatePools.setUpdate('update');
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
