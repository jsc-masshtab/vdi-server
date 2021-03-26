import { Pipe, PipeTransform, CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { TableIntoComponent } from './table-into';

// Mocked pipes
@Pipe({ name: 'rename' })
class TranslatePipe implements PipeTransform {
  transform(value: string): string {
      return value;
  }
}

@Pipe({ name: 'status' })
class StatusPipe implements PipeTransform {
  transform(value: string): string {
      return value;
  }
}

@Pipe({ name: 'assignmentType' })
class AssignmentTypePipe implements PipeTransform {
  transform(value: string): string {
      return value;
  } 
}

describe('TableIntoComponent', () => {
  let component: TableIntoComponent;
  let fixture: ComponentFixture<TableIntoComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [
        TableIntoComponent,
        TranslatePipe,
        StatusPipe,
        AssignmentTypePipe
      ],
      schemas: [
        CUSTOM_ELEMENTS_SCHEMA,
        NO_ERRORS_SCHEMA
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TableIntoComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
