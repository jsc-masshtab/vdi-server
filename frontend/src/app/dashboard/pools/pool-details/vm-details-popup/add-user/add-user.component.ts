import { Subscription } from 'rxjs';
import { WaitService } from '../../../../common/components/single/wait/wait.service';
import { Component, Inject, OnDestroy } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialog } from '@angular/material';
import { PoolDetailsService } from '../../pool-details.service';

interface IData  {
  vm: {
    id: string;
    name: string;
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
  selector: 'vdi-add-user-vm',
  templateUrl: './add-user.component.html'
})

export class AddUserVmComponent implements OnDestroy  {

  private user: string;
  private sub: Subscription;

  constructor(private waitService: WaitService,
              private poolService: PoolDetailsService,
              @Inject(MAT_DIALOG_DATA) public data: IData,
              public dialog: MatDialog
            ) {}

  public send() {
    this.waitService.setWait(true);
    this.poolService.assignVmToUser(this.data.vm.id, this.user).subscribe(() => {
      this.sub = this.poolService.getPool(this.data.idPool, this.data.typePool).subscribe(() => {
        this.waitService.setWait(false);
        this.dialog.closeAll();
      });
    });
  }

  public selectUser(value: []) {
    this.user = value['value'];
  }

  ngOnDestroy() {
    this.sub.unsubscribe();
  }

}
