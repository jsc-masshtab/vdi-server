import { Pipe, PipeTransform, CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA } from '@angular/core';
import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';

import { TableComponentComponent } from './table-component.component';

// Mocked pipes
@Pipe({ name: 'statusIcon' })
class StatusIconPipe implements PipeTransform {
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

@Pipe({ name: 'rename' })
class TranslatePipe implements PipeTransform {
  transform(value: string): string {
      return value;
  }
}

describe('TableComponentComponent', () => {
  let component: TableComponentComponent;
  let fixture: ComponentFixture<TableComponentComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        TableComponentComponent,
        StatusIconPipe,
        StatusPipe,
        AssignmentTypePipe,
        TranslatePipe
      ],
      schemas: [
        CUSTOM_ELEMENTS_SCHEMA,
        NO_ERRORS_SCHEMA
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TableComponentComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
