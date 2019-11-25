import { WaitService } from '../../../../common/components/single/wait/wait.service';
import { Component, Inject } from '@angular/core';
import { MatDialog, MAT_DIALOG_DATA } from '@angular/material';
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
  address: string;
}

@Component({
  selector: 'vdi-remove-user-vm',
  templateUrl: './remove-user.component.html'
})

export class RemoveUserVmComponent {

  constructor(private waitService: WaitService,
              private poolService: PoolDetailsService,
              public dialog: MatDialog,
              @Inject(MAT_DIALOG_DATA) public data: IData,
            ) {}

  public send() {
    this.waitService.setWait(true);
    this.poolService.freeVmFromUser(this.data.vm.id).subscribe(() => {
      this.poolService.getPool(this.data.idPool, this.data.typePool, this.data.address).subscribe(() => {
        this.waitService.setWait(false);
      });
      this.dialog.closeAll();
    });
  }

}
