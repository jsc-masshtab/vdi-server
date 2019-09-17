import { AddUserVmComponent } from './add-user/add-user.component';

import { Component, Inject, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material';
import { MatDialog } from '@angular/material';



@Component({
  selector: 'vdi-details-popup',
  templateUrl: './vm-details-popup.component.html'
})

export class VmDetalsPopupComponent  implements OnInit {

  // public pendingUsers: boolean = false;
  // public users: [] = [];
  // private id_users: [] = [];
  public menuActive:string = 'info';
  public collection_into_vm_automated:any[] = [
    {
      title: 'Название',
      property: 'name',
    },
    {
      title: 'Шаблон',
      property: "template",
      property_lv2: 'name'
    },
    {
      title: 'Состояние',
      property: "state"
    }
  ];
  
  public collection_into_vm_static:any[] = [
    {
      title: 'Название',
      property: 'name'
    },
    {
      title: 'Состояние',
      property: "state"
    }
  ];

  constructor(//private waitService: WaitService,
             // private usersService: UsersService,
             // private poolsService: PoolsService,
             public dialog: MatDialog,
             @Inject(MAT_DIALOG_DATA) public data: any
             ) {}

  ngOnInit() {
    console.log(this.data);
    //this.getUsers();
  }

  // public send() {
  //   this.waitService.setWait(true);
  //   this.usersService.entitleUsersToPool(this.data.pool_id, this.id_users).subscribe(() => {
  //     this.poolsService.getPool(this.data.pool_id, this.data.pool_type).subscribe(() => {
  //       this.waitService.setWait(false);
  //     });
  //     this.dialogRef.close();
  //   });
  // }

  // private getUsers() {
  //   this.pendingUsers = true;
  //   this.usersService.getAllUsersNoEntitleToPool(this.data.pool_id).valueChanges.pipe(map(data => data.data.pool.users))
  //   .subscribe( (data) => {
  //     this.users =  data;
  //     this.pendingUsers = false;
  //   },
  //   (error) => {
  //     this.users = [];
  //     this.pendingUsers = false;
  //   });
  // }

  // public selectUser(value:[]) {
  //   this.id_users = value['value'];
  // }

  public addUser() {
    this.dialog.open(AddUserVmComponent, {
      width: '500px',
      data: {
        data: this.data
      }
    });
  }

  public routeTo(route:string): void {
    if(route === 'info') {
      this.menuActive = 'info';
    }

    if(route === 'vms') {
      this.menuActive = 'vms';
    }

    if(route === 'users') {
      this.menuActive = 'users';
    }
  }

}
