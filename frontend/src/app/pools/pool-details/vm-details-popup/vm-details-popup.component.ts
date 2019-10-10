import { AddUserVmComponent } from './add-user/add-user.component';
import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialog } from '@angular/material';
import { RemoveUserVmComponent } from './remove-user/remove-user.component';

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
  usersPool: [{[key: string]: IPoolUser }];
  idPool: number;
}

interface IPoolUser {
  username: string;
}

@Component({
  selector: 'vdi-details-popup',
  templateUrl: './vm-details-popup.component.html'
})

export class VmDetalsPopupComponent {

  public menuActive: string = 'info';
  public collectionIntoVmAutomated: any[] = [
    {
      title: 'Название',
      property: 'name',
      type: 'string'
    },
    {
      title: 'Шаблон',
      property: 'template',
      property_lv2: 'name'
    },
    {
      title: 'Пользователь',
      property: 'user',
      property_lv2: 'username'
    }
  ];
  public collectionIntoVmStatic: any[] = [
    {
      title: 'Название',
      property: 'name',
      type: 'string'
    },
    {
      title: 'Пользователь',
      property: 'user',
      property_lv2: 'username'
    }
  ];

  constructor(public dialog: MatDialog,
              @Inject(MAT_DIALOG_DATA) public data: IData
             ) {}


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
