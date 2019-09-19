import { AddUserVmComponent } from './add-user/add-user.component';
import { Component, Inject, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialog } from '@angular/material';
import { RemoveUserVmComponent } from './remove-user/remove-user.component';

interface IVmDetails  {
  vm: {
    id: string;
    name: string;
    state: string;
  };
  pool_type: string;
  pool_users: [{[key: string]: IPoolUser }];
  pool_id: number;
}

interface IPoolUser {
  username: string;
}

@Component({
  selector: 'vdi-details-popup',
  templateUrl: './vm-details-popup.component.html'
})

export class VmDetalsPopupComponent  implements OnInit {

  public menuActive: string = 'info';
  public collection_into_vm_automated: any[] = [
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
      title: 'Пользователь',
      property: "user",
      property_lv2: 'username'
    },
    {
      title: 'Состояние',
      property: "state"
    }
  ];
  public collection_into_vm_static: any[] = [
    {
      title: 'Название',
      property: 'name'
    },
    {
      title: 'Пользователь',
      property: "user",
      property_lv2: 'username'
    },
    {
      title: 'Состояние',
      property: "state"
    }
  ];

  constructor(public dialog: MatDialog,
             @Inject(MAT_DIALOG_DATA) public data: IVmDetails
             ) {}

  ngOnInit() {
    console.log(this.data);
  }

  public addUser() {
    this.dialog.open(AddUserVmComponent, {
      width: '500px',
      data: this.data
    });
  }

  public removeUser() {
    this.dialog.open(RemoveUserVmComponent, {
      width: '500px',
      data: this.data
    });
  }

  public routeTo(route: string): void {
    if (route === 'info') {
      this.menuActive = 'info';
    }
  }

}
