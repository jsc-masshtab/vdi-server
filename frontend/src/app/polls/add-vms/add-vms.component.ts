import { WaitService } from './../../common/components/wait/wait.service';
import { VmsService } from './../../resourses/vms/vms.service';
import { PoolsService } from '../pools.service';
import { MatDialogRef } from '@angular/material';
import { Component, Inject } from '@angular/core';
import {MAT_DIALOG_DATA} from '@angular/material';
import { map } from 'rxjs/operators';


@Component({
  selector: 'vdi-add-vms-static-pool',
  templateUrl: './add-vms.component.html'
})

export class AddVMStaticPoolComponent  {

  public pendingVms:boolean = false;
  public vms: [] = [];
  private id_vms: [] = [];

  constructor(private poolService: PoolsService,
              private vmsService: VmsService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<AddVMStaticPoolComponent>,
              @Inject(MAT_DIALOG_DATA) public data: any) {}

  ngOnInit() {
    this.getVms();
  }
 
  public send() {
    this.waitService.setWait(true);
    this.poolService.addVMStaticPool(this.data.pool_id,this.id_vms).subscribe(() => {
      this.dialogRef.close();
      this.poolService.getPool(this.data.pool_id,this.data.pool_type).subscribe();
      this.waitService.setWait(false);
    });
  }

  private getVms() {
    this.pendingVms = true;
    this.vmsService.getAllVms(this.data.id_cluster,this.data.id_node).valueChanges.pipe(map(data => data.data.list_of_vms))
    .subscribe( (data) => {
      this.vms =  data;
      this.pendingVms = false;
    },
    (error)=> {
      this.vms = [];
      this.pendingVms = false;
    });
  }

  public selectVm(value:[]) {
    this.id_vms = value['value'];
  }

}
