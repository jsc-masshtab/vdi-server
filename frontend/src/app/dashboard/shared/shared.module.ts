import { AddSelectComponent } from './components/add-select/add-select';
import { AppRoutingModule } from '../../app-routing.module';


import { MatDialogModule } from '@angular/material/dialog';
import { StatusPipe } from './pipes/statusEntity.pipe';
import { PoolTypePipe } from './pipes/poolType.pipe';
import { TaskTypePipe } from './pipes/taskType.pipe';
import { CommonModule } from '@angular/common';
import { FocusMeDirective } from './directives/focusMe.directive';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgModule } from '@angular/core';
import { TableIntoComponent } from './components/table-into-component/table-into';
import { TableComponentComponent } from './components/table-component/table-component.component';
import { FormForEditComponent } from './forms-dinamic/change-form/form-edit.component';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatSelectModule } from '@angular/material/select';
import { PaginationComponent } from './components/pagination/pagination.component';
import { FooterService } from '../core/components/footer/footer.service';
import { YesNoFormComponent } from './forms-dinamic/yes-no-form/yes-no-form.component';
import { TranslatePipe } from './pipes/translate.pipe';
import { AssignmentTypePipe } from './pipes/assignmentType.pipe';
import { StatusIconPipe } from './pipes/statusIcon.pipe';



const COMPONENTS = [
  TableComponentComponent,
  TableIntoComponent,
  PaginationComponent,
  AddSelectComponent
];

const DIRECTIVES = [
  FocusMeDirective
];

const PIPES = [
  StatusPipe,
  StatusIconPipe,
  AssignmentTypePipe,
  TranslatePipe,
  PoolTypePipe,
  TaskTypePipe
];

const FORMS_DINAMIC = [
  FormForEditComponent,
  YesNoFormComponent
];


@NgModule({
  declarations: [
    ...DIRECTIVES,
    ...PIPES,
    ...FORMS_DINAMIC,
    ...COMPONENTS
  ],
  exports: [
    ...DIRECTIVES,
    ...COMPONENTS,
    ...PIPES,
    ...FORMS_DINAMIC
  ],
  imports: [
    CommonModule,
    FontAwesomeModule,
    MatDialogModule,
    ReactiveFormsModule,
    MatCheckboxModule,
    MatSelectModule,
    AppRoutingModule,
    FormsModule
  ],
  providers: [
    FooterService
  ]
})


export class SharedModule {

  constructor() {}



}
