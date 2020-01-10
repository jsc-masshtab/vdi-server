import { IParams } from '../../../../../../types';
import { WaitService } from '../../../common/components/single/wait/wait.service';
import { AddUserComponent } from '../add-auth-directory/add-auth-directory.component';
import { Component, OnInit, OnDestroy } from '@angular/core';
import { AuthenticationDirectoryService   } from '../auth-directory.service';
import { map } from 'rxjs/operators';
import { MatDialog } from '@angular/material';


@Component({
  selector: 'vdi-all-auth-directory',
  templateUrl: './all-auth-directory.component.html',
  styleUrls: ['./all-auth-directory.component.scss']
})


export class AuthenticationDirectoryComponent implements OnInit, OnDestroy {

  public authDirectory: [];
  public collection: object[] = [
    {
      title: 'Имя пользователя',
      property: 'auth-directoryname',
      class: 'name-start',
      icon: 'users',
      type: 'string',
      sort: true
    },
    /*{
      title: 'Дата создания',
      property: 'date_joined',
      type: 'time',
      reverse_sort: true
    }*/
  ];

  constructor(private service: AuthenticationDirectoryService, public dialog: MatDialog, private waitService: WaitService) {}

  ngOnInit() {
    this.getAllAuthenticationDirectory();
  }

  public addUser() {
    this.dialog.open(AddUserComponent, {
      width: '500px'
    });
  }

  public getAllAuthenticationDirectory() {
    this.waitService.setWait(true);
    this.service.getAllAuthenticationDirectory().valueChanges.pipe(map(data => data.data.authDirectory))
      .subscribe((data) => {
        this.authDirectory = data;
        this.waitService.setWait(false);
    });
  }

  public sortList(param: IParams): void  {
    this.service.paramsForGetAuthenticationDirectory.spin = param.spin;
    this.service.paramsForGetAuthenticationDirectory.nameSort = param.nameSort;
    this.getAllAuthenticationDirectory();
  }

  ngOnDestroy() {
    this.service.paramsForGetAuthenticationDirectory.spin = true;
    this.service.paramsForGetAuthenticationDirectory.nameSort = undefined;
  }
}
