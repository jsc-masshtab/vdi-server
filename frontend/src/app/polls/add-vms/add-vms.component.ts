import { VmsService } from './../../resourses/vms/vms.service';
import { PoolsService } from '../pools.service';
import { MatDialogRef } from '@angular/material';
import { Component, Inject } from '@angular/core';
import { Router } from '@angular/router';
import {MAT_DIALOG_DATA} from '@angular/material';
import { map } from 'rxjs/operators';


@Component({
  selector: 'vdi-add-vms-static-pool',
  templateUrl: './add-vms.component.html'
})

export class AddVMStaticPoolComponent  {

  public pendingVms:boolean = false;
  public vms = {};

  constructor(private service: PoolsService,
              private vmsService: VmsService,
              private dialogRef: MatDialogRef<AddVMStaticPoolComponent>,
              private router: Router,
              @Inject(MAT_DIALOG_DATA) public data: any) {}

  ngOnInit() {
    this.getVms();
  }
 
  // public send() {
  //   this.service.removePool(this.data.pool_id).subscribe((res) => {
  //     this.dialogRef.close();
  //     setTimeout(()=> {
  //       this.router.navigate([`pools`]);
  //       this.service.getAllPools().subscribe();
  //     },1000); 
    
  //   },(error) => {
      
  //   });
  // }

  private getVms() {
    this.pendingVms = true;
    console.log(this.data);
    this.vmsService.getAllVms(this.data.id_cluster,this.data.id_node,this.data.id_datapool).valueChanges.pipe(map(data => data.data.list_of_vms))
    .subscribe( (data) => {
      this.vms =  data;
      console.log(data);
      this.pendingVms = false;
    },
    (error)=> {
      this.vms = [];
      this.pendingVms = false;
    });
  }

  public selectVm(value:[]) {
    // let id_vms: [] = [];
    // id_vms = value['value'].map(vm => vm['id']);
    // this.createPoolForm.get('vm_ids_list').setValue(id_vms);
    // this.finishPoll['vm_name'] = value['value'].map(vm => vm['name']);
  }

}
