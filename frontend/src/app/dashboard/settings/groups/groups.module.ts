import { RemoveGroupComponent } from './remove-groups/remove-group.component';
import { RemoveUserGroupComponent } from './groups-details/remove-user/remove-user.component';

import { AddGroupComponent } from './add-groups/add-groups.component';
import { GroupsComponent } from './all-groups/groups.component';
import { MatSelectModule } from '@angular/material/select';
import { MatDialogModule } from '@angular/material/dialog';
import { AppRoutingModule } from '../../../app-routing.module';
import { SharedModule } from '../../common/shared.module';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';

import { GroupsDetailsComponent } from './groups-details/groups-details.component';
import { MatCheckboxModule, MatInputModule } from '@angular/material';
import { GroupsService } from './groups.service';
import { AddRoleComponent } from './groups-details/add-role/add-role.component';
import { RemoveRoleComponent } from './groups-details/remove-role/remove-role.component';
import { AddUserGroupComponent } from './groups-details/add-users/add-user.component';




@NgModule({
   declarations: [
      GroupsComponent,
      AddGroupComponent,
      GroupsDetailsComponent,
      AddRoleComponent,
      RemoveRoleComponent,
      AddUserGroupComponent,
      RemoveUserGroupComponent,
      RemoveGroupComponent
   ],
   imports: [
      SharedModule,
      CommonModule,
      FontAwesomeModule,
      AppRoutingModule,
      MatDialogModule,
      MatSelectModule,
      ReactiveFormsModule,
      MatCheckboxModule,
      MatInputModule
   ],
   providers: [
      GroupsService
   ],
   exports: [
      GroupsComponent
   ],
   entryComponents: [
      AddGroupComponent,
      AddRoleComponent,
      RemoveRoleComponent,
      AddUserGroupComponent,
      RemoveUserGroupComponent,
      RemoveGroupComponent
   ]
})
export class GroupsModule { }
