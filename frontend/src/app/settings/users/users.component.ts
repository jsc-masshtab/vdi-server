import { Component, OnInit } from '@angular/core';
import { UsersService   } from './users.service';
import { map } from 'rxjs/operators';


@Component({
  selector: 'vdi-users',
  templateUrl: './users.component.html',
  styleUrls: ['./users.component.scss']
})


export class UsersComponent implements OnInit {

  public users: [];
  public collection: object[] = [
    {
      title: '№',
      property: 'index'
    },
    {
      title: 'Имя пользователя',
      property: 'username'
    }
  ];
  public crumbs: object[] = [
    {
      title: 'Настройки',
      icon: 'cog'
    },
    {
      title: 'Пользователи',
      icon: 'users'
    }
  ];

  public spinner:boolean = false;

  constructor(private service: UsersService){}

  ngOnInit() {
    this.getAllUsers();
  }

  private getAllUsers() {
    this.spinner = true;
    this.service.getAllUsers().valueChanges.pipe(map(data => data.data.users))
      .subscribe((data) => {
        this.users = data;
        this.spinner = false;
      },
      (error) => {
        this.spinner = false;
      });
  }
}
