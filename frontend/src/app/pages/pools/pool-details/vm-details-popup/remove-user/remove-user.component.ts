import { Component, Inject } from '@angular/core';
import { MatDialog, MAT_DIALOG_DATA } from '@angular/material/dialog';

import { WaitService } from '../../../../../core/components/wait/wait.service';
import { PoolDetailsService } from '../../pool-details.service';

interface IData  {
  vm: {
    id: string;
    verbose_name: string;
    state: string;
    user: {
      username: string | null;
    };
    template?: {
      name: string;
    }
  };
  typePool: string;
  usersPool: [{username: string }];
  idPool: number;
}

@Component({
  selector: 'vdi-remove-user-vm',
  templateUrl: './remove-user.component.html'
})

export class RemoveUserVmComponent {

  private user: string;
  public valid: boolean = true;

  constructor(private waitService: WaitService,
              private poolService: PoolDetailsService,
              public dialog: MatDialog,
              @Inject(MAT_DIALOG_DATA) public data: IData,
            ) {}

  public send() {
    if (this.user) {
      this.waitService.setWait(true);
      this.poolService.freeVmFromUser(this.data.vm.id, this.user).subscribe((res) => {
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

  public selectUser(value: []) {
    this.user = value['value'];
    this.valid = true;
  }
}
