import { IParams } from '../../../../../../types';
import { WaitService } from '../../../common/components/single/wait/wait.service';
import { AddGroupComponent } from '../add-groups/add-groups.component';
import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { GroupsService   } from '../groups.service';
import { map } from 'rxjs/operators';
import { MatDialog } from '@angular/material';
import { Subscription } from 'rxjs';
import { Router } from '@angular/router';
import { DetailsMove } from '../../../common/classes/details-move';


@Component({
  selector: 'vdi-groups',
  templateUrl: './groups.component.html',
  styleUrls: ['./groups.component.scss']
})


export class GroupsComponent extends DetailsMove implements OnInit, OnDestroy {

  private getGroupsSub: Subscription;

  public groups: [];
  public collection: object[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      icon: 'users-cog',
      type: 'string',
      sort: true
    },
    {
      title: 'Описание',
      property: 'description',
      type: 'string',
      sort: true
    },
    {
      title: 'Пользователи',
      property: 'assigned_users',
      type: 'array-length'
    }
  ];

  constructor(private service: GroupsService, public dialog: MatDialog, private waitService: WaitService,
              private router: Router) {
    super();
  }

  @ViewChild('view') view: ElementRef;

  ngOnInit() {
    this.getAllGroups();
  }

  public addGroup() {
    this.dialog.open(AddGroupComponent, {
 			disableClose: true, 
      width: '500px'
    });
  }

  public getAllGroups() {
    if (this.getGroupsSub) {
      this.getGroupsSub.unsubscribe();
    }

    this.waitService.setWait(true);

    this.service.getGroups().valueChanges.pipe(map(data => data.data.groups))
      .subscribe((data) => {
        this.groups = data;
        this.waitService.setWait(false);
    });
  }

  public refresh(): void {
    this.service.paramsForGetUsers.spin = true;
    this.getAllGroups();
  }

  public sortList(param: IParams): void  {
    this.service.paramsForGetUsers.spin = param.spin;
    this.service.paramsForGetUsers.nameSort = param.nameSort;
    this.getAllGroups();
  }

  public routeTo(event): void {
    this.router.navigate([`pages/settings/groups/${event.id}`]);
  }

  public onResize(): void {
    super.onResize(this.view);
  }

  public componentActivate(): void {
    super.componentActivate(this.view);
  }

  public componentDeactivate(): void {
    super.componentDeactivate();
  }

  ngOnDestroy() {
    this.service.paramsForGetUsers.spin = true;
    this.service.paramsForGetUsers.nameSort = undefined;

    if (this.getGroupsSub) {
      this.getGroupsSub.unsubscribe();
    }
  }
}
