import { IParams } from '../../../../../../../types';
import { WaitService } from '../../../../core/components/wait/wait.service';
import { AddAuthenticationDirectoryComponent } from '../add-auth-directory/add-auth-directory.component';
import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { AuthenticationDirectoryService   } from '../auth-directory.service';
import { map } from 'rxjs/operators';
import { MatDialog } from '@angular/material/dialog';
import { Subscription } from 'rxjs';
import { DetailsMove } from '../../../../common/classes/details-move';
import { Router } from '@angular/router';


@Component({
  selector: 'vdi-all-auth-directory',
  templateUrl: './all-auth-directory.component.html',
  styleUrls: ['./all-auth-directory.component.scss']
})


export class AuthenticationDirectoryComponent extends DetailsMove implements OnInit, OnDestroy {

  private getAllAuthenticationDirectorySub: Subscription;

  public authDirectory: [];
  public collection: object[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      icon: 'address-card',
      type: 'string',
      sort: true
    },
    {
      title: 'Cтатус',
      property: 'status',
      sort: true
    }
  ];

  constructor(private service: AuthenticationDirectoryService, public dialog: MatDialog, private waitService: WaitService,
              private router: Router) {
    super();
  }

  @ViewChild('view', { static: true }) view: ElementRef;

  ngOnInit() {
    this.getAllAuthenticationDirectory();
  }

  public addUser() {
    this.dialog.open(AddAuthenticationDirectoryComponent, {
      disableClose: true, 
      width: '500px'
    });
  }

  public getAllAuthenticationDirectory() {

    if (this.getAllAuthenticationDirectorySub) {
      this.getAllAuthenticationDirectorySub.unsubscribe();
    }

    this.waitService.setWait(true);

    this.getAllAuthenticationDirectorySub = this.service.getAllAuthenticationDirectory().valueChanges.pipe(map(data => data.data))
      .subscribe((data) => {
        this.authDirectory = data.auth_dirs;
        this.waitService.setWait(false);
    });
  }

  public refresh(): void {
    this.service.paramsForGetAuthenticationDirectory.spin = true;
    this.getAllAuthenticationDirectory();
  }

  public routeTo(event): void {
    this.router.navigate([`pages/settings/auth-directory/${event.id}`]);
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

  public sortList(param: IParams): void  {
    this.service.paramsForGetAuthenticationDirectory.spin = param.spin;
    this.service.paramsForGetAuthenticationDirectory.nameSort = param.nameSort;
    this.getAllAuthenticationDirectory();
  }

  ngOnDestroy() {
    this.service.paramsForGetAuthenticationDirectory.spin = true;
    this.service.paramsForGetAuthenticationDirectory.nameSort = undefined;

    if (this.getAllAuthenticationDirectorySub) {
      this.getAllAuthenticationDirectorySub.unsubscribe();
    }
  }
}
