import { WaitService } from './../../common/components/wait/wait.service';
import { PoolsService } from './../pools.service';
import { MatDialogRef } from '@angular/material';
import { Component, Inject } from '@angular/core';
import { Router } from '@angular/router';
import {MAT_DIALOG_DATA} from '@angular/material';


@Component({
  selector: 'vdi-remove-pool',
  templateUrl: './remove-pool.component.html'
})

export class RemovePoolComponent  {


  constructor(private service: PoolsService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<RemovePoolComponent>,
              private router: Router,
              @Inject(MAT_DIALOG_DATA) public data: any) {}

    
  public send() {
    this.waitService.setWait(true);
    this.service.removePool(this.data.pool_id).subscribe((res) => {
      this.dialogRef.close();
      setTimeout(()=> {
        this.router.navigate([`pools`]);
        this.service.getAllPools().subscribe();
        this.waitService.setWait(false);
      },1000); 
    });
  }

}
