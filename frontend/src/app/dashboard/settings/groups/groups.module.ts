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
import { MatCheckboxModule } from '@angular/material';
import { GroupsService } from './groups.service';




@NgModule({
   declarations: [
      GroupsComponent,
      AddGroupComponent,
      GroupsDetailsComponent
   ],
   imports: [
      SharedModule,
      CommonModule,
      FontAwesomeModule,
      AppRoutingModule,
      MatDialogModule,
      MatSelectModule,
      ReactiveFormsModule,
      MatCheckboxModule
   ],
   providers: [
      GroupsService
   ],
   exports: [
      GroupsComponent
   ],
   entryComponents: [
      AddGroupComponent
   ]
})
export class GroupsModule { }
