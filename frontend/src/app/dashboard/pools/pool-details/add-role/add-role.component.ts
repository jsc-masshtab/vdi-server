import { PoolDetailsService } from '../pool-details.service';

import { MatDialogRef } from '@angular/material';
import { Component, Inject, OnDestroy } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { WaitService } from 'src/app/dashboard/common/components/single/wait/wait.service';
import { PoolsUpdateService } from '../../all-pools/pools.update.service';

@Component({
  selector: 'vdi-add-role',
  templateUrl: './add-role.component.html'
})

export class AddRoleComponent implements OnDestroy {

  public pending: boolean = false;
  public roles: [] = [];
  private destroy: Subject<any> = new Subject<any>();
  public valid: boolean = true;

  constructor(private service: PoolDetailsService,
              private updatePools: PoolsUpdateService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<AddRoleComponent>,
              @Inject(MAT_DIALOG_DATA) public data: any) { }



  public send() {
    if (this.roles.length) {
      this.waitService.setWait(true);
      this.service.addRole(this.data.id, this.roles)
        .pipe(takeUntil(this.destroy)).subscribe((res) => {
          if (res) {
            this.service.getPool(this.data.id, this.data.typePool).refetch();
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
    this.roles = value['value'];
    this.valid = true;
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }

}
