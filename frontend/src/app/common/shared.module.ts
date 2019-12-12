import { AppRoutingModule } from './../app-routing.module';
import { WaitService } from './components/single/wait/wait.service';

import { MainMenuComponent } from './components/single/main-menu/main-menu.component';
import { FooterComponent } from './components/single/footer/footer.component';
import { ShellComponent } from './components/single/shell/shell.component';
import { MatDialogModule } from '@angular/material/dialog';
import { StatusPipe, StatusIconPipe } from './pipes/statusEntity.pipes';
import { CommonModule } from '@angular/common';
import { FocusMeDirective } from './directives/focusMe.directive';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgModule } from '@angular/core';
import { TableIntoComponent } from './components/shared/table-into-component/table-into';
import { TableComponentComponent } from './components/shared/table-component/table-component.component';
import { FormForEditComponent } from './forms-dinamic/change-form/form-edit.component';
import { ReactiveFormsModule } from '@angular/forms';
import { MatCheckboxModule } from '@angular/material';
import { WaitComponent } from './components/single/wait/wait.component';


const COMPONENTS = [
  TableComponentComponent,
  TableIntoComponent,
  ShellComponent,
  FooterComponent,
  MainMenuComponent,
  WaitComponent
];

const DIRECTIVES = [
  FocusMeDirective
];

const PIPES = [
  StatusPipe,
  StatusIconPipe
];

const FORMS_DINAMIC = [
  FormForEditComponent
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
    AppRoutingModule
  ],
  providers: [WaitService],
  entryComponents: [
    ...FORMS_DINAMIC
  ]
})


export class SharedModule {

  constructor() {}



}
